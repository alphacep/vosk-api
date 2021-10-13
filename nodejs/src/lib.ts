import os from 'os'
import path from 'path'
import ffi from 'ffi-napi'
import ref from 'ref-napi'

const vosk_model = ref.types.void
const vosk_model_ptr = ref.refType(vosk_model)
const vosk_spk_model = ref.types.void
const vosk_spk_model_ptr = ref.refType(vosk_spk_model)
const vosk_recognizer = ref.types.void
const vosk_recognizer_ptr = ref.refType(vosk_recognizer)

let soname
if (os.platform() === 'win32') {
  soname = path.join(__dirname, '../lib', 'win-x86_64', 'libvosk.dll')
} else if (os.platform() === 'darwin') {
  soname = path.join(__dirname, '../lib', 'osx-x86_64', 'libvosk.dylib')
} else {
  soname = path.join(__dirname, '../lib', 'linux-x86_64', 'libvosk.so')
}

export type VoskModel = typeof vosk_model_ptr
export type VoskSpkModel = typeof vosk_spk_model_ptr
export type VoskRecognizer = typeof vosk_recognizer_ptr

interface VoskLibrary {
  /** Loads model data from the file and returns the model object
   *
   * @param model_path: the path of the model on the filesystem
   * @returns model object or NULL if problem occured
   */
  vosk_model_new: {
    (modelPath: string): VoskModel | null
    async: (
      modelPath: string,
      cb: (err: Error | null, model: VoskModel | null) => void,
    ) => void
  }

  /** Releases the model memory
   *
   *  The model object is reference-counted so if some recognizer
   *  depends on this model, model might still stay alive. When
   *  last recognizer is released, model will be released too.
   */
  vosk_model_free: (model: VoskModel) => void

  /** Check if a word can be recognized by the model
   * @param word: the word
   * @returns the word symbol if @param word exists inside the model
   * or -1 otherwise.
   * Reminding that word symbol 0 is for <epsilon>
   */
  vosk_model_find_word: (model: VoskModel, word: string) => number

  /** Loads speaker model data from the file and returns the model object
   *
   * @param model_path: the path of the model on the filesystem
   * @returns model object or NULL if problem occured
   */
  vosk_spk_model_new: {
    (modelPath: string): VoskSpkModel | null
    async: (
      modelPath: string,
      cb: (err: Error | null, model: VoskSpkModel | null) => void,
    ) => void
  }

  /** Releases the model memory
   *
   *  The model object is reference-counted so if some recognizer
   *  depends on this model, model might still stay alive. When
   *  last recognizer is released, model will be released too.
   */
  vosk_spk_model_free: (model: VoskSpkModel) => void

  /** Creates the recognizer object
   *
   *  The recognizers process the speech and return text using shared model data
   *  @param sample_rate The sample rate of the audio you going to feed into the recognizer
   *  @returns recognizer object or NULL if problem occured
   */
  vosk_recognizer_new: (
    model: VoskModel,
    sampleRate: number,
  ) => VoskRecognizer | null

  /** Creates the recognizer object with speaker recognition
   *
   *  With the speaker recognition mode the recognizer not just recognize
   *  text but also return speaker vectors one can use for speaker identification
   *
   *  @param spk_model speaker model for speaker identification
   *  @param sample_rate The sample rate of the audio you going to feed into the recognizer
   *  @returns recognizer object or NULL if problem occured
   */
  vosk_recognizer_new_spk: (
    model: VoskModel,
    sampleRate: number,
    spkModel: VoskSpkModel,
  ) => VoskRecognizer | null

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
   *  @param sampleRate The sample rate of the audio you going to feed into the recognizer
   *  @param grammar The string with the list of phrases to recognize as JSON array of strings,
   *                 for example "["one two three four five", "[unk]"]".
   *
   *  @returns recognizer object or NULL if problem occured
   */
  vosk_recognizer_new_grm: (
    model: VoskModel,
    sampleRate: number,
    grammar: string,
  ) => VoskRecognizer | null

  /**
   * Configures recognizer to output n-best results
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
   * @param maxAlternatives - maximum alternatives to return from recognition results
   */
  vosk_recognizer_set_max_alternatives: (
    recognizer: VoskRecognizer,
    maxAlternatives: number,
  ) => void

  /**
   * Configures recognizer to output words with times
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
   */
  vosk_recognizer_set_words: (
    recognizer: VoskRecognizer,
    words: boolean,
  ) => void

  /** Adds speaker recognition model to already created recognizer. Helps to initialize
   * speaker recognition for grammar-based recognizer.
   *
   * @param spkModel Speaker recognition model
   */
  vosk_recognizer_set_spk_model: (
    recognizer: VoskRecognizer,
    spkModel: VoskSpkModel,
  ) => void

  /** Accept voice data
   *
   *  accept and process new chunk of voice data
   *
   *  @param data - audio data in PCM 16-bit mono format
   *  @param length - length of the audio data
   *  @returns 1 if silence is occured and you can retrieve a new utterance with result method
   *           0 if decoding continues
   *           -1 if exception occured
   */
  vosk_recognizer_accept_waveform: {
    (recognizer: VoskRecognizer, data: Buffer, dataLength: number): number
    async: (
      recognizer: VoskRecognizer,
      data: Buffer,
      dataLength: number,
      cb: (err: Error | null, endOfSpeech: number) => void,
    ) => void
  }

  /** Returns speech recognition result
   *
   * @returns the result in JSON format which contains decoded line, decoded
   *          words, times in seconds and confidences. You can parse this result
   *          with any json parser
   *
   * <pre>
   * {
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
   *      "end" : 2.610000,
   *       "start" : 2.340000,
   *       "word" : "one"
   *     }],
   *   "text" : "what zero zero zero one"
   *  }
   * </pre>
   */
  vosk_recognizer_result: (recognizer: VoskRecognizer) => string

  /** Returns partial speech recognition
   *
   * @returns partial speech recognition text which is not yet finalized.
   *          result may change as recognizer process more data.
   *
   * <pre>
   * {
   *  "partial" : "cyril one eight zero"
   * }
   * </pre>
   */
  vosk_recognizer_partial_result: (recognizer: VoskRecognizer) => string

  /** Returns speech recognition result. Same as result, but doesn't wait for silence
   *  You usually call it in the end of the stream to get final bits of audio. It
   *  flushes the feature pipeline, so all remaining audio chunks got processed.
   *
   *  @returns speech result in JSON format.
   */
  vosk_recognizer_final_result: (recognizer: VoskRecognizer) => string

  /** Releases recognizer object
   *
   *  Underlying model is also unreferenced and if needed released */
  vosk_recognizer_free: (recognizer: VoskRecognizer) => void

  /**
   *
   * Resets current results so the recognition can continue from scratch
   */
  vosk_recognizer_reset: (recognizer: VoskRecognizer) => void

  /** Set log level for Kaldi messages
   *
   *  @param log_level the level
   *     0 - default value to print info and error messages but no debug
   *     less than 0 - don't print info messages
   *     greather than 0 - more verbose mode
   */
  vosk_set_log_level: (logLevel: number) => void

  /**
   *  Init, automatically select a CUDA device and allow multithreading.
   *  Must be called once from the main thread.
   *  Has no effect if HAVE_CUDA flag is not set.
   */
  vosk_gpu_init: () => void

  /**
   *  Init CUDA device in a multi-threaded environment.
   *  Must be called for each thread.
   *  Has no effect if HAVE_CUDA flag is not set.
   */
  vosk_gpu_thread_init: () => void
}

const libvosk: VoskLibrary = ffi.Library(soname, {
  vosk_model_new: [vosk_model_ptr, ['string']],
  vosk_model_free: ['void', [vosk_model_ptr]],
  vosk_model_find_word: ['int', [vosk_model_ptr, 'string']],
  vosk_spk_model_new: [vosk_spk_model_ptr, ['string']],
  vosk_spk_model_free: ['void', [vosk_spk_model_ptr]],
  vosk_recognizer_new: [vosk_recognizer_ptr, [vosk_model_ptr, 'float']],
  vosk_recognizer_new_spk: [
    vosk_recognizer_ptr,
    [vosk_model_ptr, 'float', vosk_spk_model_ptr],
  ],
  vosk_recognizer_new_grm: [
    vosk_recognizer_ptr,
    [vosk_model_ptr, 'float', 'string'],
  ],
  vosk_recognizer_set_max_alternatives: ['void', [vosk_recognizer_ptr, 'int']],
  vosk_recognizer_set_words: ['void', [vosk_recognizer_ptr, 'bool']],
  vosk_recognizer_set_spk_model: [
    'void',
    [vosk_recognizer_ptr, vosk_spk_model_ptr],
  ],
  vosk_recognizer_accept_waveform: [
    'bool',
    [vosk_recognizer_ptr, 'pointer', 'int'],
  ],
  vosk_recognizer_result: ['string', [vosk_recognizer_ptr]],
  vosk_recognizer_partial_result: ['string', [vosk_recognizer_ptr]],
  vosk_recognizer_final_result: ['string', [vosk_recognizer_ptr]],
  vosk_recognizer_free: ['void', [vosk_recognizer_ptr]],
  vosk_recognizer_reset: ['void', [vosk_recognizer_ptr]],
  vosk_set_log_level: ['void', ['int']],
  vosk_gpu_init: ['void', []],
  vosk_gpu_thread_init: ['void', []],
})

export default libvosk
