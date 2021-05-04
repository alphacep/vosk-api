// Copyright 2020 Alpha Cephei Inc.
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
#include "kaldi_recognizer.h"
#include "model.h"
#include "spk_model.h"

#if HAVE_CUDA
#include "cudamatrix/cu-device.h"
#endif

#include <string.h>

using namespace kaldi;

VoskModel *vosk_model_new(const char *model_path)
{
    try {
        return (VoskModel *)new Model(model_path);
    } catch (...) {
        return nullptr;
    }
}

void vosk_model_free(VoskModel *model)
{
    if (model == nullptr) {
       return;
    }
    ((Model *)model)->Unref();
}

int vosk_model_find_word(VoskModel *model, const char *word)
{
    return (int) ((Model *)model)->FindWord(word);
}

VoskSpkModel *vosk_spk_model_new(const char *model_path)
{
    try {
        return (VoskSpkModel *)new SpkModel(model_path);
    } catch (...) {
        return nullptr;
    }
}

void vosk_spk_model_free(VoskSpkModel *model)
{
    if (model == nullptr) {
       return;
    }
    ((SpkModel *)model)->Unref();
}

VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate)
{
    try {
        return (VoskRecognizer *)new KaldiRecognizer((Model *)model, sample_rate);
    } catch (...) {
        return nullptr;
    }
}

VoskRecognizer *vosk_recognizer_new_spk(VoskModel *model, float sample_rate, VoskSpkModel *spk_model)
{
    try {
        return (VoskRecognizer *)new KaldiRecognizer((Model *)model, sample_rate, (SpkModel *)spk_model);
    } catch (...) {
        return nullptr;
    }
}

VoskRecognizer *vosk_recognizer_new_grm(VoskModel *model, float sample_rate, const char *grammar)
{
    try {
        return (VoskRecognizer *)new KaldiRecognizer((Model *)model, sample_rate, grammar);
    } catch (...) {
        return nullptr;
    }
}

void vosk_recognizer_set_max_alternatives(VoskRecognizer *recognizer, int max_alternatives)
{
    ((KaldiRecognizer *)recognizer)->SetMaxAlternatives(max_alternatives);
}

void vosk_recognizer_set_result_options(VoskRecognizer *recognizer, const char *result_opts)
{
    ((KaldiRecognizer *)recognizer)->SetResultOptions(result_opts);
}

void vosk_recognizer_set_words(VoskRecognizer *recognizer, int words)
{
    ((KaldiRecognizer *)recognizer)->SetWords((bool)words);
}

void vosk_recognizer_set_spk_model(VoskRecognizer *recognizer, VoskSpkModel *spk_model)
{
    if (recognizer == nullptr || spk_model == nullptr) {
       return;
    }
    ((KaldiRecognizer *)recognizer)->SetSpkModel((SpkModel *)spk_model);
}

int vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length)
{
    try {
        return ((KaldiRecognizer *)(recognizer))->AcceptWaveform(data, length);
    } catch (...) {
        return -1;
    }
}

int vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length)
{
    try {
        return ((KaldiRecognizer *)(recognizer))->AcceptWaveform(data, length);
    } catch (...) {
        return -1;
    }
}

int vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length)
{
    try {
        return ((KaldiRecognizer *)(recognizer))->AcceptWaveform(data, length);
    } catch (...) {
        return -1;
    }
}

const char *vosk_recognizer_result(VoskRecognizer *recognizer)
{
    return ((KaldiRecognizer *)recognizer)->Result();
}

const char *vosk_recognizer_partial_result(VoskRecognizer *recognizer)
{
    return ((KaldiRecognizer *)recognizer)->PartialResult();
}

const char *vosk_recognizer_final_result(VoskRecognizer *recognizer)
{
    return ((KaldiRecognizer *)recognizer)->FinalResult();
}

void vosk_recognizer_reset(VoskRecognizer *recognizer)
{
    ((KaldiRecognizer *)recognizer)->Reset();
}

void vosk_recognizer_free(VoskRecognizer *recognizer)
{
    delete (KaldiRecognizer *)(recognizer);
}

void vosk_set_log_level(int log_level)
{
    SetVerboseLevel(log_level);
}

void vosk_gpu_init()
{
#if HAVE_CUDA
    kaldi::CuDevice::Instantiate().SelectGpuId("yes");
    kaldi::CuDevice::Instantiate().AllowMultithreading();
#endif
}

void vosk_gpu_thread_init()
{
#if HAVE_CUDA
    kaldi::CuDevice::Instantiate();
#endif
}
