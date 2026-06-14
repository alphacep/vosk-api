// Copyright 2020-2021 Alpha Cephei Inc.
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

/* This header contains the C API for Vosk speech recognition system */

#ifndef VOSK_API_H
#define VOSK_API_H

#ifdef __cplusplus
extern "C" {
#endif

/** Model stores all the data required for recognition
 *  it contains static data and can be shared across processing
 *  threads. */
typedef struct VoskModel VoskModel;


/** Speaker model is the same as model but contains the data
 *  for speaker identification. */
typedef struct VoskSpkModel VoskSpkModel;


/** Recognizer object is the main object which processes data.
 *  Each recognizer usually runs in own thread and takes audio as input.
 *  Once audio is processed recognizer returns JSON object as a string
 *  which represent decoded information - words, confidences, times, n-best lists,
 *  speaker information and so on */
typedef struct VoskRecognizer VoskRecognizer;

/** Inverse text normalization */
typedef struct VoskTextProcessor VoskTextProcessor;

/**
 * Batch model object
 */
typedef struct VoskBatchModel VoskBatchModel;

/**
 * Batch recognizer object
 */
typedef struct VoskBatchRecognizer VoskBatchRecognizer;


/** Loads model data from the file and returns the model object
 *
 * @param model_path: the path of the model on the filesystem
 * @returns model object or NULL if problem occured */
VoskModel *vosk_model_new(const char *model_path);


/** Releases the model memory
 *
 *  The model object is reference-counted so if some recognizer
 *  depends on this model, model might still stay alive. When
 *  last recognizer is released, model will be released too. */
void vosk_model_free(VoskModel *model);


/** Check if a word can be recognized by the model
 * @param word: the word
 * @returns the word symbol if @param word exists inside the model
 * or -1 otherwise.
 * Reminding that word symbol 0 is for <epsilon> */
int vosk_model_find_word(VoskModel *model, const char *word);


/** Loads speaker model data from the file and returns the model object
 *
 * @param model_path: the path of the model on the filesystem
 * @returns model object or NULL if problem occurred */
VoskSpkModel *vosk_spk_model_new(const char *model_path);


/** Releases the model memory
 *
 *  The model object is reference-counted so if some recognizer
 *  depends on this model, model might still stay alive. When
 *  last recognizer is released, model will be released too. */
void vosk_spk_model_free(VoskSpkModel *model);

/** Creates the recognizer object
 *
 *  The recognizers process the speech and return text using shared model data
 *  @param model       VoskModel containing static data for recognizer. Model can be
 *                     shared across recognizers, even running in different threads.
 *  @param sample_rate The sample rate of the audio you going to feed into the recognizer.
 *                     Make sure this rate matches the audio content, it is a common
 *                     issue causing accuracy problems.
 *  @returns recognizer object or NULL if problem occured */
VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate);


/** Creates the recognizer object with speaker recognition
 *
 *  With the speaker recognition mode the recognizer not just recognize
 *  text but also return speaker vectors one can use for speaker identification
 *
 *  @param model       VoskModel containing static data for recognizer. Model can be
 *                     shared across recognizers, even running in different threads.
 *  @param sample_rate The sample rate of the audio you going to feed into the recognizer.
 *                     Make sure this rate matches the audio content, it is a common
 *                     issue causing accuracy problems.
 *  @param spk_model speaker model for speaker identification
 *  @returns recognizer object or NULL if problem occured */
VoskRecognizer *vosk_recognizer_new_spk(VoskModel *model, float sample_rate, VoskSpkModel *spk_model);


/** Creates the recognizer object with the phrase list
 *
 *  Sometimes when you want to improve recognition accuracy and when you don't need
 *  to recognize large vocabulary you can specify a list of phrases to recognize. This
 *  will improve recognizer speed and accuracy but might return [unk] if user said
 *  something different.
 *
 *  Only recognizers with lookahead models support this type of quick configuration.
 *  Precompiled HCLG graph models are not supported.
 *
 *  @param model       VoskModel containing static data for recognizer. Model can be
 *                     shared across recognizers, even running in different threads.
 *  @param sample_rate The sample rate of the audio you going to feed into the recognizer.
 *                     Make sure this rate matches the audio content, it is a common
 *                     issue causing accuracy problems.
 *  @param grammar The string with the list of phrases to recognize as JSON array of strings,
 *                 for example "["one two three four five", "[unk]"]".
 *
 *  @returns recognizer object or NULL if problem occured */
VoskRecognizer *vosk_recognizer_new_grm(VoskModel *model, float sample_rate, const char *grammar);


/** Adds speaker model to already initialized recognizer
 *
 * Can add speaker recognition model to already created recognizer. Helps to initialize
 * speaker recognition for grammar-based recognizer.
 *
 * @param spk_model Speaker recognition model */
void vosk_recognizer_set_spk_model(VoskRecognizer *recognizer, VoskSpkModel *spk_model);


/** Reconfigures recognizer to use grammar
 *
 * @param recognizer   Already running VoskRecognizer
 * @param grammar      Set of phrases in JSON array of strings or "[]" to use default model graph.
 *                     See also vosk_recognizer_new_grm
 */
void vosk_recognizer_set_grm(VoskRecognizer *recognizer, char const *grammar);


/** Configures recognizer to output n-best results
 *
 * <pre>
 *   {
 *      "alternatives": [
 *          { "text": "one two three four five", "confidence": 0.97 },
 *          { "text": "one two three for five", "confidence": 0.03 },
 *      ]
 *   }
 * </pre>
 *
 * @param max_alternatives - maximum alternatives to return from recognition results
 */
void vosk_recognizer_set_max_alternatives(VoskRecognizer *recognizer, int max_alternatives);

/** Configures recognizer result options (i.e. whether to print word-level results or word and phone level results together)
 * With phone level results (i.e. if configured with "phones" option)
 * <pre>
 *    {
 *     "result" : [{
 *         "conf" : 0.998335,
 *         "end" : 0.450000,
 *         "phone_end" : [0.450000],
 *         "phone_label" : ["SIL"],
 *         "phone_start" : [0.000000],
 *         "start" : 0.000000,
 *         "word" : "<eps>"
 *       }, {
 *         "conf" : 0.998324,
 *         "end" : 0.600000,
 *         "phone_end" : [0.540000, 0.600000],
 *         "phone_label" : ["DH_B", "AH1_E"],
 *         "phone_start" : [0.450000, 0.540000],
 *         "start" : 0.450000,
 *         "word" : "THE"
 *       }, {
 *         "conf" : 0.574095,
 *         "end" : 1.200000,
 *         "phone_end" : [0.720000, 0.810000, 0.870000, 0.930000, 0.990000, 1.080000, 1.110000, 1.200000],
 *         "phone_label" : ["S_B", "T_I", "UW1_I", "D_I", "AH0_I", "N_I", "T_I", "S_E"],
 *         "phone_start" : [0.600000, 0.720000, 0.810000, 0.870000, 0.930000, 0.990000, 1.080000, 1.110000],
 *         "start" : 0.600000,
 *         "word" : "STUDENT'S"
 *       }, {
 *         "conf" : 0.923344,
 *         "end" : 1.260000,
 *         "phone_end" : [1.260111],
 *         "phone_label" : ["SIL"],
 *         "phone_start" : [1.200111],
 *         "start" : 1.200111,
 *         "word" : "<eps>"
 *       }, {
 *         "conf" : 1.000000,
 *         "end" : 1.800000,
 *         "phone_end" : [1.440000, 1.500000, 1.590000, 1.680000, 1.800000],
 *         "phone_label" : ["S_B", "T_I", "AH1_I", "D_I", "IY0_E"],
 *         "phone_start" : [1.260000, 1.440000, 1.500000, 1.590000, 1.680000],
 *         "start" : 1.260000,
 *         "word" : "STUDY"
 *       }, {
 *         "conf" : 1.000000,
 *         "end" : 1.860000,
 *         "phone_end" : [1.860000],
 *         "phone_label" : ["AH0_S"],
 *         "phone_start" : [1.800000],
 *         "start" : 1.800000,
 *         "word" : "A"
 *       }, {
 *         "conf" : 1.000000,
 *         "end" : 2.190000,
 *         "phone_end" : [1.980000, 2.100000, 2.190000],
 *         "phone_label" : ["L_B", "AA1_I", "T_E"],
 *         "phone_start" : [1.860000, 1.980000, 2.100000],
 *         "start" : 1.860000,
 *         "word" : "LOT"
 *       }, {
 *         "conf" : 1.000000,
 *         "end" : 2.880000,
 *         "phone_end" : [2.880000],
 *         "phone_label" : ["SIL"],
 *         "phone_start" : [2.190000],
 *         "start" : 2.190000,
 *         "word" : "<eps>"
 *       }],
 *     "text" : " THE STUDENT'S STUDY A LOT"
 *   }
 * </pre>
 *
 * If configured with "words" option then result is same word-level MBR results. See vosk_recognizer_result() 
 * </pre>
 * * @param result_opts - result options to determine which recognition results to return
 */
void vosk_recognizer_set_result_options(VoskRecognizer *recognizer, const char *result_opts);

/** Enables words with times in the output
 *
 * <pre>
 *   "result" : [{
 *       "conf" : 1.000000,
 *       "end" : 1.110000,
 *       "start" : 0.870000,
 *       "word" : "what"
 *     }, {
 *       "conf" : 1.000000,
 *       "end" : 1.530000,
 *       "start" : 1.110000,
 *       "word" : "zero"
 *     }, {
 *       "conf" : 1.000000,
 *       "end" : 1.950000,
 *       "start" : 1.530000,
 *       "word" : "zero"
 *     }, {
 *       "conf" : 1.000000,
 *       "end" : 2.340000,
 *       "start" : 1.950000,
 *       "word" : "zero"
 *     }, {
 *       "conf" : 1.000000,
 *       "end" : 2.610000,
 *       "start" : 2.340000,
 *       "word" : "one"
 *     }],
 * </pre>
 *
 * @param words - boolean value
 */
void vosk_recognizer_set_words(VoskRecognizer *recognizer, int words);

/** Like above return words and confidences in partial results
 *
 * @param partial_words - boolean value
 */
void vosk_recognizer_set_partial_words(VoskRecognizer *recognizer, int partial_words);

/** Set NLSML output
 * @param nlsml - boolean value
 */
void vosk_recognizer_set_nlsml(VoskRecognizer *recognizer, int nlsml);

typedef enum VoskEpMode {
    VOSK_EP_ANSWER_DEFAULT = 0,
    VOSK_EP_ANSWER_SHORT = 1,
    VOSK_EP_ANSWER_LONG = 2,
    VOSK_EP_ANSWER_VERY_LONG = 3,
} VoskEndpointerMode;

/**
 * Set endpointer scaling factor
 *
 * @param mode - Endpointer mode
 **/
void vosk_recognizer_set_endpointer_mode(VoskRecognizer *recognizer,  VoskEndpointerMode mode);

/**
 * Set endpointer delays
 *
 * @param t_start_max     timeout for stopping recognition in case of initial silence (usually around 5.0)
 * @param t_end           timeout for stopping recognition in milliseconds after we recognized something (usually around 0.5 - 1.0)
 * @param t_max           timeout for forcing utterance end in milliseconds (usually around 20-30)
 **/
void vosk_recognizer_set_endpointer_delays(VoskRecognizer *recognizer, float t_start_max, float t_end, float t_max);

/** Accept voice data
 *
 *  accept and process new chunk of voice data
 *
 *  @param data - audio data in PCM 16-bit mono format
 *  @param length - length of the audio data
 *  @returns 1 if silence is occured and you can retrieve a new utterance with result method 
 *           0 if decoding continues
 *           -1 if exception occured */
int vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length);


/** Same as above but the version with the short data for language bindings where you have
 *  audio as array of shorts */
int vosk_recognizer_accept_waveform_s(VoskRecognizer *recognizer, const short *data, int length);


/** Same as above but the version with the float data for language bindings where you have
 *  audio as array of floats */
int vosk_recognizer_accept_waveform_f(VoskRecognizer *recognizer, const float *data, int length);


/** Returns speech recognition result
 *
 * @returns the result in JSON format which contains decoded line, decoded
 *          words, times in seconds and confidences. You can parse this result
 *          with any json parser
 *
 * <pre>
 *  {
 *    "text" : "what zero zero zero one"
 *  }
 * </pre>
 *
 * If alternatives enabled it returns result with alternatives, see also vosk_recognizer_set_max_alternatives().
 *
 * If word times enabled returns word time, see also vosk_recognizer_set_word_times().
 */
const char *vosk_recognizer_result(VoskRecognizer *recognizer);


/** Returns partial speech recognition
 *
 * @returns partial speech recognition text which is not yet finalized.
 *          result may change as recognizer process more data.
 *
 * <pre>
 * {
 *    "partial" : "cyril one eight zero"
 * }
 * </pre>
 */
const char *vosk_recognizer_partial_result(VoskRecognizer *recognizer);


/** Returns speech recognition result. Same as result, but doesn't wait for silence
 *  You usually call it in the end of the stream to get final bits of audio. It
 *  flushes the feature pipeline, so all remaining audio chunks got processed.
 *
 *  @returns speech result in JSON format.
 */
const char *vosk_recognizer_final_result(VoskRecognizer *recognizer);


/** Resets the recognizer
 *
 *  Resets current results so the recognition can continue from scratch */
void vosk_recognizer_reset(VoskRecognizer *recognizer);


/** Releases recognizer object
 *
 *  Underlying model is also unreferenced and if needed released */
void vosk_recognizer_free(VoskRecognizer *recognizer);

/** Set log level for Kaldi messages
 *
 *  @param log_level the level
 *     0 - default value to print info and error messages but no debug
 *     less than 0 - don't print info messages
 *     greater than 0 - more verbose mode
 */
void vosk_set_log_level(int log_level);

/**
 *  Init, automatically select a CUDA device and allow multithreading.
 *  Must be called once from the main thread.
 *  Has no effect if HAVE_CUDA flag is not set.
 */
void vosk_gpu_init();

/**
 *  Init CUDA device in a multi-threaded environment.
 *  Must be called for each thread.
 *  Has no effect if HAVE_CUDA flag is not set.
 */
void vosk_gpu_thread_init();

/** Creates the batch recognizer object
 *
 *  @returns model object or NULL if problem occured */
VoskBatchModel *vosk_batch_model_new(const char *model_path);

/** Releases batch model object */
void vosk_batch_model_free(VoskBatchModel *model);

/** Wait for the processing */
void vosk_batch_model_wait(VoskBatchModel *model);

/** Creates batch recognizer object
 *  @returns recognizer object or NULL if problem occured */
VoskBatchRecognizer *vosk_batch_recognizer_new(VoskBatchModel *model, float sample_rate);
 
/** Releases batch recognizer object */
void vosk_batch_recognizer_free(VoskBatchRecognizer *recognizer);

/** Accept batch voice data */
void vosk_batch_recognizer_accept_waveform(VoskBatchRecognizer *recognizer, const char *data, int length);

/** Set NLSML output
 * @param nlsml - boolean value
 */
void vosk_batch_recognizer_set_nlsml(VoskBatchRecognizer *recognizer, int nlsml);

/** Closes the stream */
void vosk_batch_recognizer_finish_stream(VoskBatchRecognizer *recognizer);

/** Return results */
const char *vosk_batch_recognizer_front_result(VoskBatchRecognizer *recognizer);

/** Release and free first retrieved result */
void vosk_batch_recognizer_pop(VoskBatchRecognizer *recognizer);

/** Get amount of pending chunks for more intelligent waiting */
int vosk_batch_recognizer_get_pending_chunks(VoskBatchRecognizer *recognizer);

/** Create text processor */
VoskTextProcessor *vosk_text_processor_new(const char *tagger, const char *verbalizer);

/** Release text processor */
void vosk_text_processor_free(VoskTextProcessor *processor);

/** Convert string */
char *vosk_text_processor_itn(VoskTextProcessor *processor, const char *input);

#ifdef __cplusplus
}
#endif

#endif /* VOSK_API_H */
