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
    int pending;

    std::queue<std::string> results;
    std::queue<std::vector<float>> input;
    LinearResample *resampler;
    std::vector<float> buffer;
};


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
                for (auto itr = model->active.begin(); itr != model->active.end(); itr++) {
                    VoskRecognizer *recognizer = *itr;

                    while (!recognizer->input.empty()) {
                        std::vector<float> &data = recognizer->input.front();
                        recognizer->vad->AcceptWaveform(data.data(), data.size());
                        if (!recognizer->vad->Empty()) {
                            SpeechSegment segment = recognizer->vad->Front();
                            std::unique_ptr<OfflineStream> stream = model->recognizer->CreateStream();
                            stream->AcceptWaveform(recognizer->sample_rate, segment.samples.data(), segment.samples.size());
    	    	            p_streams.push_back(stream.get());
                            streams.push_back(std::move(stream));
                            p_recs.push_back(recognizer);
                            recognizer->vad->Pop();
                            recognizer->pending++;
                        }
                        recognizer->input.pop();
                    }
                    recognizer->pending--; // We processed current queue
                }
                // Delete inactive
                for (auto itr = model->active.begin(); itr != model->active.end();) {
                    VoskRecognizer *recognizer = *itr;
                    if (recognizer->pending == 0) {
                         model->active.erase(itr++);
                    } else {
                        ++ itr;
                    }
                }
            }
        }

        size = p_streams.size();
        if (size > 0) {
            SHERPA_ONNX_LOGE("Running batch of %d chunks", size);
            model->recognizer->DecodeStreams(p_streams.data(), size);
            SHERPA_ONNX_LOGE("Done running batch of %d chunks", size);

            std::unique_lock<std::mutex> lock(model->active_lock);
            for (int i = 0; i < size; i++) {
                p_recs[i]->results.push(std::string("{\"text\" : \"") + streams[i]->GetResult().text + "\"}");
                streams[i].reset();
                p_recs[i]->pending--;
                if (p_recs[i]->pending == 0) {
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
    rec->pending = 0;
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

    // Pick chunks and submit them to the batcher
    std::vector<float>::const_iterator first = recognizer->buffer.begin();
    std::vector<float>::const_iterator second = recognizer->buffer.begin() + SAMPLES_PER_CHUNK;

    // Queue chunks
    while (second < recognizer->buffer.end()) {
        std::vector<float> chunk(first, second);
        recognizer->input.push(chunk);
        first += SAMPLES_PER_CHUNK;
        second += SAMPLES_PER_CHUNK;
    }

    // Keep remaining data
    int i = first - recognizer->buffer.begin();
    if (i > 0) {
        int tail = recognizer->buffer.size() - i;
        for (int j = 0; j < tail; j++) {
            recognizer->buffer[j] = recognizer->buffer[i + j];
        }
        recognizer->buffer.resize(tail);
     }

    {
        std::unique_lock<std::mutex> lock(recognizer->model->active_lock);
        recognizer->model->active.insert(recognizer);
        recognizer->pending++;
    }
}

const char *vosk_recognizer_result_front(VoskRecognizer *recognizer)
{
    if (recognizer->results.empty()) {
       return "{\"partial\" : \"\"}";
    }
    return recognizer->results.front().c_str();
}

void vosk_recognizer_result_pop(VoskRecognizer *recognizer)
{
    if (!recognizer->results.empty()) {
        recognizer->results.pop();
    }
}

/** Get amount of pending chunks for more intelligent waiting */
int vosk_recognizer_get_pending_results(VoskRecognizer *recognizer)
{
    return recognizer->pending;
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
