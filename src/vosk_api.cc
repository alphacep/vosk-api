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

#include <string>
#include <iostream>

using namespace sherpa_onnx;

struct VoskModel {
    std::string model_path_str;
    std::shared_ptr<OfflineRecognizer> recognizer;
};

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
      config.max_active_paths = 10;
      config.feat_config.sampling_rate = 16000;
      config.feat_config.feature_dim = 80;

      model->recognizer = std::make_shared<OfflineRecognizer>(config);

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
    model->recognizer.reset();
    delete model;
}

struct VoskRecognizer {
    VoiceActivityDetector *vad;
    std::shared_ptr<OfflineRecognizer> recognizer;
    float sample_rate;
    std::string last_result;
};

VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate)
{
    VoskRecognizer *rec = new VoskRecognizer;

    VadModelConfig vad_config;
    vad_config.silero_vad.model = model->model_path_str + "/vad/vad.onnx";
    vad_config.silero_vad.min_silence_duration = 0.25;
    rec->vad = new VoiceActivityDetector(vad_config);
    rec->sample_rate = sample_rate;
    rec->recognizer = model->recognizer;
    return rec;
}

int vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length)
{
    float wave[length / 2];
    for (int i = 0; i < length / 2; i++) {
        wave[i] = *(((short *)data) + i) / 32768.;
    }
    return vosk_recognizer_accept_waveform_f(recognizer, wave, length / 2);
}

int vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length)
{
    float wave[length];
    for (int i = 0; i < length / 2; i++)
        wave[i] = data[i];
    return vosk_recognizer_accept_waveform_f(recognizer, wave, length);
}

int vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length)
{
    recognizer->vad->AcceptWaveform(data, length);
    if (recognizer->vad->Empty()) {
         return 0;
    }

    SpeechSegment segment = recognizer->vad->Front();
    auto stream = recognizer->recognizer->CreateStream();
    stream->AcceptWaveform(recognizer->sample_rate, segment.samples.data(), segment.samples.size());
    recognizer->vad->Pop();
    recognizer->recognizer->DecodeStream(stream.get());
    OfflineRecognitionResult res = stream->GetResult();
    recognizer->last_result = "{\"text\" : \"" + res.text + "\"}";
    stream.reset();
    return 1;
}

const char *vosk_recognizer_result(VoskRecognizer *recognizer)
{
    return recognizer->last_result.c_str();
}

const char *vosk_recognizer_partial_result(VoskRecognizer *recognizer)
{
    return "{\"partial\" : \"\"}";
}

const char *vosk_recognizer_final_result(VoskRecognizer *recognizer)
{
    if (!recognizer->vad->IsSpeechDetected()) {
        return "{\"text\" : \"\"}";
    }
    return "{\"text\" : \"\"}";
}

void vosk_recognizer_reset(VoskRecognizer *recognizer)
{
    // Nothing here for now
}

void vosk_recognizer_free(VoskRecognizer *recognizer)
{
    recognizer->recognizer.reset();
    delete recognizer->vad;
    delete recognizer;
}

void vosk_set_log_level(int log_level)
{
    // Nothing for now
}
