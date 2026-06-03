// Copyright 2020-2024 Alpha Cephei Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#include "vosk_api.h"
#include "offline-recognizer.h"
#include "voice-activity-detector.h"
#include "offline-stream.h"
#include "macros.h"
#include "resample.h"

#include <algorithm>
#include <atomic>
#include <chrono>
#include <condition_variable>
#include <cstring>
#include <memory>
#include <mutex>
#include <queue>
#include <set>
#include <string>
#include <thread>
#include <vector>

using namespace sherpa_onnx;

struct VoskModel {
    std::string model_path_str;
    std::shared_ptr<OfflineRecognizer> recognizer;

    std::mutex active_lock;
    // Signaled whenever a recognizer's processing/input state changes so that
    // vosk_recognizer_free() can wait for in-flight work to drain.
    std::condition_variable state_cv;
    std::set<VoskRecognizer *> active;
    std::thread recognizer_thread;
    std::atomic<bool> running{false};
};

struct VoskRecognizer {
    std::unique_ptr<VoiceActivityDetector> vad;
    std::unique_ptr<LinearResample> resampler;
    VoskModel *model = nullptr;
    float sample_rate = 0.0f;

    std::queue<std::string> results;
    std::queue<std::vector<float>> input;
    int processing = 0;
    std::vector<float> buffer;
};

#define BATCH_SIZE 32

namespace {

// A group of streams to be decoded together, keeping the stream owners and the
// originating recognizers aligned by index.
struct Batch {
    std::vector<std::unique_ptr<OfflineStream>> streams;
    std::vector<OfflineStream *> p_streams;
    std::vector<VoskRecognizer *> p_recs;

    size_t size() const { return streams.size(); }

    void add(std::unique_ptr<OfflineStream> stream, VoskRecognizer *rec) {
        p_streams.push_back(stream.get());
        streams.push_back(std::move(stream));
        p_recs.push_back(rec);
    }
};

}  // namespace

void recognizer_loop(VoskModel *model)
{
    // Decode one collected batch and publish the results back to the
    // originating recognizers. Takes the model lock to mutate shared state.
    auto run_batch = [model](Batch &batch) {
        if (batch.size() == 0) {
            return;
        }

        int batch_size = static_cast<int>(batch.size());
        SHERPA_ONNX_LOGE("Running batch of %d chunks", batch_size);
        model->recognizer->DecodeStreams(batch.p_streams.data(), batch_size);
        SHERPA_ONNX_LOGE("Done running batch of %d chunks", batch_size);

        std::unique_lock<std::mutex> lock(model->active_lock);
        for (int i = 0; i < batch_size; i++) {
            VoskRecognizer *rec = batch.p_recs[i];
            rec->results.push("{\"text\" : \"" + batch.streams[i]->GetResult().text + "\"}");
            batch.streams[i].reset();
            rec->processing--;
            if (rec->input.empty() && rec->processing == 0) {
                model->active.erase(rec);
            }
        }
        model->state_cv.notify_all();
    };

    while (model->running) {
        // Three queues partition work by chunk length so that similarly sized
        // streams are batched together (unless USE_ONE_QUEUE is defined).
        Batch batches[3];
        auto total = [&batches] {
            return batches[0].size() + batches[1].size() + batches[2].size();
        };

        {
            std::unique_lock<std::mutex> lock(model->active_lock);
            // Collect chunks into a batch, preferably from different recognizers.
            while (true) {
                int added = 0;
                for (VoskRecognizer *recognizer : model->active) {
                    if (recognizer->input.empty()) {
                        continue;
                    }
                    const std::vector<float> &samples = recognizer->input.front();
                    SHERPA_ONNX_LOGE("Processing chunk of %d samples",
                                     static_cast<int>(samples.size()));
                    std::unique_ptr<OfflineStream> stream = model->recognizer->CreateStream();
                    stream->AcceptWaveform(16000, samples.data(), samples.size());

#ifdef USE_ONE_QUEUE
                    int idx = 0;
#else
                    int idx = (samples.size() < 30000) ? 0
                            : (samples.size() < 100000) ? 1
                            : 2;
#endif
                    batches[idx].add(std::move(stream), recognizer);

                    recognizer->input.pop();
                    recognizer->processing++;
                    added++;

                    if (total() >= BATCH_SIZE) {
                        break;
                    }
                }
                // Nothing left to collect, or the batch is full.
                if (added == 0 || total() >= BATCH_SIZE) {
                    break;
                }
            }
        }

        if (total() == 0) {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            continue;
        }

        for (Batch &batch : batches) {
            run_batch(batch);
        }
    }
}

VoskModel *vosk_model_new(const char *model_path)
{
    try {
        auto model = std::make_unique<VoskModel>();

        OfflineRecognizerConfig config;

        config.model_config.debug = 0;
        config.model_config.num_threads = 0;
        config.model_config.provider = "cuda";
        config.model_config.model_type = "transducer";

        model->model_path_str = model_path;
        config.model_config.tokens = model->model_path_str + "/lang/tokens.txt";
        config.model_config.transducer.encoder_filename = model->model_path_str + "/am-onnx/encoder.onnx";
        config.model_config.transducer.decoder_filename = model->model_path_str + "/am-onnx/decoder.onnx";
        config.model_config.transducer.joiner_filename = model->model_path_str + "/am-onnx/joiner.onnx";

        config.decoding_method = "modified_beam_search";
        config.max_active_paths = 10;
        config.feat_config.sampling_rate = 16000;
        config.feat_config.feature_dim = 80;

        model->recognizer = std::make_shared<OfflineRecognizer>(config);

        model->running = true;
        model->recognizer_thread = std::thread(recognizer_loop, model.get());

        return model.release();
    } catch (...) {
        return nullptr;
    }
}

void vosk_model_free(VoskModel *model)
{
    if (model == nullptr) {
        return;
    }
    model->running = false;
    // Wake any vosk_recognizer_free() that is waiting on the worker to drain.
    model->state_cv.notify_all();
    if (model->recognizer_thread.joinable()) {
        model->recognizer_thread.join();
    }
    delete model;
}


VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate)
{
    auto rec = std::make_unique<VoskRecognizer>();

    VadModelConfig vad_config;
    vad_config.silero_vad.model = model->model_path_str + "/vad/vad.onnx";
    rec->vad = std::make_unique<VoiceActivityDetector>(vad_config);
    rec->sample_rate = sample_rate;
    rec->model = model;
    rec->resampler = std::make_unique<LinearResample>(
        sample_rate, 16000.0f,
        std::min(sample_rate, 16000.0f) / 2, 16);
    return rec.release();
}

void vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length)
{
    int num_samples = length / 2;
    std::vector<float> wave(num_samples);
    const short *samples = reinterpret_cast<const short *>(data);
    for (int i = 0; i < num_samples; i++) {
        wave[i] = samples[i] / 32768.0f;
    }
    vosk_recognizer_accept_waveform_f(recognizer, wave.data(), num_samples);
}

void vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length)
{
    std::vector<float> wave(length);
    for (int i = 0; i < length; i++) {
        wave[i] = data[i] / 32768.0f;
    }
    vosk_recognizer_accept_waveform_f(recognizer, wave.data(), length);
}

#define SAMPLES_PER_CHUNK 1024
void vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length)
{
    std::vector<float> resampled_data;
    recognizer->resampler->Resample(data, length, false, &resampled_data);

    recognizer->buffer.insert(recognizer->buffer.end(), resampled_data.begin(), resampled_data.end());

    size_t i;
    for (i = 0; i + SAMPLES_PER_CHUNK < recognizer->buffer.size(); i += SAMPLES_PER_CHUNK) {
        recognizer->vad->AcceptWaveform(recognizer->buffer.data() + i, SAMPLES_PER_CHUNK);
        if (!recognizer->vad->Empty()) {
            std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
            SpeechSegment segment = recognizer->vad->Front();
            recognizer->input.push(segment.samples);
            recognizer->model->active.insert(recognizer);
            recognizer->vad->Pop();
        }
    }

    if (i > 0) {
        recognizer->buffer.erase(recognizer->buffer.begin(), recognizer->buffer.begin() + i);
    }
}

void vosk_recognizer_flush(VoskRecognizer *recognizer)
{
    if (!recognizer->vad->IsSpeechDetected()) {
        return;
    }

    // Flush remaining signal, zero-padded to a full chunk.
    std::vector<float> buf(SAMPLES_PER_CHUNK, 0.0f);
    size_t n = std::min(recognizer->buffer.size(), static_cast<size_t>(SAMPLES_PER_CHUNK));
    std::copy(recognizer->buffer.begin(), recognizer->buffer.begin() + n, buf.begin());
    recognizer->vad->AcceptWaveform(buf.data(), SAMPLES_PER_CHUNK);
    recognizer->vad->Flush();

    {
        std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
        SpeechSegment segment = recognizer->vad->Front();
        recognizer->input.push(segment.samples);
        recognizer->model->active.insert(recognizer);
        recognizer->vad->Pop();
    }
}

const char *vosk_recognizer_result_front(VoskRecognizer *recognizer)
{
    std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
    return recognizer->results.front().c_str();
}

void vosk_recognizer_result_pop(VoskRecognizer *recognizer)
{
    std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
    recognizer->results.pop();
}

/** Get number of pending chunks for more intelligent waiting */
int vosk_recognizer_get_num_pending_results(VoskRecognizer *recognizer)
{
    std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
    return recognizer->input.size() + recognizer->processing;
}

int vosk_recognizer_get_num_results(VoskRecognizer *recognizer)
{
    std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
    return recognizer->results.size();
}

int vosk_recognizer_results_empty(VoskRecognizer *recognizer)
{
    std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
    return recognizer->results.empty();
}

void vosk_recognizer_reset(VoskRecognizer *recognizer)
{
    // Nothing here for now
}

void vosk_recognizer_set_endpointer_mode(VoskRecognizer *recognizer,  VoskEndpointerMode mode)
{
    float t_start_max, t_end, t_max;

    switch(mode) {
        case VOSK_EP_ANSWER_DEFAULT:
           t_start_max = 5.0;
           t_end = 0.5;
           t_max = 19.0;
           break;
        case VOSK_EP_ANSWER_SHORT:
           t_start_max = 5.0;
           t_end = 0.3;
           t_max = 10.0;
           break;
        case VOSK_EP_ANSWER_LONG:
           t_start_max = 10.0;
           t_end = 2.0;
           t_max = 19.0;
           break;
        case VOSK_EP_ANSWER_VERY_LONG:
           t_start_max = 10.0;
           t_end = 3.0;
           t_max = 19.0;
           break;
        default:
           t_start_max = 5.0;
           t_end = 0.5;
           t_max = 19.0;
           break;
    }
    vosk_recognizer_set_endpointer_delays(recognizer, t_start_max, t_end, t_max);
}

void vosk_recognizer_set_endpointer_delays(VoskRecognizer *recognizer, float t_start_max, float t_end, float t_max)
{
    recognizer->vad->SetEndpointerDelays(t_start_max, t_end, t_max);
}

void vosk_recognizer_free(VoskRecognizer *recognizer)
{
    if (recognizer == nullptr) {
        return;
    }

    VoskModel *model = recognizer->model;
    if (model != nullptr) {
        // Wait until the worker thread is no longer referencing this recognizer
        // (no queued input and nothing in flight) before destroying it, then
        // drop it from the active set.
        std::unique_lock<std::mutex> lock(model->active_lock);
        model->state_cv.wait(lock, [model, recognizer] {
            // Stop waiting once the worker has drained this recognizer, or if
            // the worker is no longer running (model already being freed).
            return !model->running ||
                   (recognizer->processing == 0 && recognizer->input.empty());
        });
        model->active.erase(recognizer);
    }

    delete recognizer;
}

void vosk_set_log_level(int log_level)
{
    // Nothing for now
}
