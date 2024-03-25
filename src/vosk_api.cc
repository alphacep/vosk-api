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

#include <string>
#include <iostream>
#include <chrono>
#include <thread>
#include <set>
#include <queue>
#include <string>

using namespace sherpa_onnx;

struct VoskModel {
    std::string model_path_str;
    std::shared_ptr<OfflineRecognizer> recognizer;

    std::mutex active_lock;
    std::set<VoskRecognizer *> active;
    std::thread recognizer_thread;
    bool running;
};

struct VoskRecognizer {
    VoiceActivityDetector *vad;
    VoskModel *model;
    float sample_rate;

    std::queue<std::string> results;
    std::queue<std::vector<float>> input;
    int processing;
    LinearResample *resampler;
    std::vector<float> buffer;
};

#define BATCH_SIZE 16

void recognizer_loop(VoskModel *model)
{
    while (model->running) {
        int size = 0;
        std::vector<std::unique_ptr<OfflineStream>> streams;
        std::vector<OfflineStream *> p_streams;
        std::vector<VoskRecognizer *> p_recs;

        {
            std::unique_lock<std::mutex> lock(model->active_lock);
            size = model->active.size();
            if (size > 0) {
                // Collect chunks into batch preferably from different recognizers
                while (true) {
                    int added = 0;
                    for (auto itr = model->active.begin(); itr != model->active.end(); itr++) {
                        VoskRecognizer *recognizer = *itr;
                        if (recognizer->input.empty()) {
                            continue;
                        }
                        added++;
                        std::vector<float> samples = recognizer->input.front();
                        std::unique_ptr<OfflineStream> stream = model->recognizer->CreateStream();
                        stream->AcceptWaveform(16000, samples.data(), samples.size());
                        p_streams.push_back(stream.get());
                        streams.push_back(std::move(stream));
                        p_recs.push_back(recognizer);
                        recognizer->input.pop();
                        recognizer->processing++;
                    }
                    if (added == 0)
                        break;
                    if (streams.size() > BATCH_SIZE)
                        break;
                }
            }
        }

        int batch_size = streams.size();
        if (batch_size > 0) {
            SHERPA_ONNX_LOGE("Running batch of %d chunks", batch_size);
            model->recognizer->DecodeStreams(p_streams.data(), batch_size);
            SHERPA_ONNX_LOGE("Done running batch of %d chunks", batch_size);

            std::unique_lock<std::mutex> lock(model->active_lock);
            for (int i = 0; i < batch_size; i++) {
                p_recs[i]->results.push(std::string("{\"text\" : \"") + streams[i]->GetResult().text + "\"}");
                streams[i].reset();
                p_recs[i]->processing--;
                if (p_recs[i]->input.empty() && p_recs[i]->processing == 0) {
                    model->active.erase(p_recs[i]);
                }
            }
        } else {
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
    }
}

VoskModel *vosk_model_new(const char *model_path)
{
    try {

      VoskModel *model = new VoskModel;

      OfflineRecognizerConfig config;

      config.model_config.debug = 0;
      config.model_config.num_threads = 8;
      config.model_config.provider = "cpu";
      config.model_config.model_type = "transducer";

      model->model_path_str = model_path;
      config.model_config.tokens = model->model_path_str + "/lang/tokens.txt";
      config.model_config.transducer.encoder_filename = model->model_path_str + "/am-onnx/encoder.onnx";
      config.model_config.transducer.decoder_filename = model->model_path_str + "/am-onnx/decoder.onnx";
      config.model_config.transducer.joiner_filename = model->model_path_str + "/am-onnx/joiner.onnx";

      config.decoding_method = "modified_beam_search";
      config.max_active_paths = 5;
      config.feat_config.sampling_rate = 16000;
      config.feat_config.feature_dim = 80;

      model->recognizer = std::make_shared<OfflineRecognizer>(config);

      model->running = true;
      model->recognizer_thread = std::thread(recognizer_loop, model);

      return model;
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
    model->recognizer_thread.join();
    model->recognizer.reset();
    delete model;
}


VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate)
{
    VoskRecognizer *rec = new VoskRecognizer;

    VadModelConfig vad_config;
    vad_config.silero_vad.model = model->model_path_str + "/vad/vad.onnx";
    vad_config.silero_vad.min_silence_duration = 0.25;
    rec->vad = new VoiceActivityDetector(vad_config);
    rec->sample_rate = sample_rate;
    rec->model = model;
    rec->resampler = new LinearResample(
        sample_rate, 16000.0f,
        std::min(sample_rate / 2, 16000.0f / 2), 6);
    return rec;
}

void vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length)
{
    float wave[length / 2];
    for (int i = 0; i < length / 2; i++) {
        wave[i] = *(((short *)data) + i) / 32768.;
    }
    return vosk_recognizer_accept_waveform_f(recognizer, wave, length / 2);
}

void vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length)
{
    float wave[length];
    for (int i = 0; i < length / 2; i++)
        wave[i] = data[i];
    return vosk_recognizer_accept_waveform_f(recognizer, wave, length);
}

#define SAMPLES_PER_CHUNK 512
void vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length)
{
    std::vector<float> resampled_data;
    recognizer->resampler->Resample(data, length, true, &resampled_data);

    recognizer->buffer.insert(std::end(recognizer->buffer), std::begin(resampled_data), std::end(resampled_data));

    int i;
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

void vosk_recognizer_free(VoskRecognizer *recognizer)
{
    delete recognizer->vad;
    delete recognizer;
}

void vosk_set_log_level(int log_level)
{
    // Nothing for now
}
