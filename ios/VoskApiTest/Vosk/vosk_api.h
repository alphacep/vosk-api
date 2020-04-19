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


#ifndef _VOSK_API_H_
#define _VOSK_API_H_

#ifdef __cplusplus
extern "C" {
#endif

typedef struct VoskModel VoskModel;
typedef struct VoskSpkModel VoskSpkModel;
typedef struct VoskRecognizer VoskRecognizer;

VoskModel *vosk_model_new(const char *model_path);
void vosk_model_free(VoskModel *model);

VoskSpkModel *vosk_spk_model_new(const char *model_path);
void vosk_spk_model_free(VoskSpkModel *model);

VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate);
VoskRecognizer *vosk_recognizer_new_spk(VoskModel *model, VoskSpkModel *spk_model, float sample_rate);
VoskRecognizer *vosk_recognizer_new_grm(VoskModel *model, float sample_rate, const char *grammar);
int vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length);
int vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length);
int vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length);
const char *vosk_recognizer_result(VoskRecognizer *recognizer);
const char *vosk_recognizer_partial_result(VoskRecognizer *recognizer);
const char *vosk_recognizer_final_result(VoskRecognizer *recognizer);
void vosk_recognizer_free(VoskRecognizer *recognizer);

#ifdef __cplusplus
}
#endif

#endif /* _VOSK_API_H_ */
