import lib, { VoskRecognizer } from './lib'
import Model from './model'
import SpkModel from './spkModel'

export interface WordInfo {
  /**
   * The confidence rate in the detection. 0 For unlikely, and 1 for totally accurate
   */
  conf: number
  /**
   * The start of the timeframe when the word is pronounced in seconds
   */
  start: number
  /**
   * The end of the timeframe when the word is pronounced in seconds
   */
  end: number
  /**
   * The word detected
   */
  word: string
}

export interface PartialResult {
  /**
   * The partial sentence that have been detected until now
   */
  partial: string
}

export interface Result {
  /**
   * Details about the words that have been detected
   */
  result: WordInfo[]
  /**
   * The complete utterance that have been detected
   */
  text: string
  /**
   * A floating vector representing speaker identity. It is usually about 128 numbers which uniquely represent speaker voice
   */
  spk?: number[]
  /**
   * The number of frames used to extract speaker vector. The more frames you have the more reliable is speaker vector
   */
  spk_frames?: number
}

/**
 * Recognizer options
 */
export interface Options {
  /**
   * The Model instance to use for speech to text
   * @see models [models](https://alphacephei.com/vosk/models)
   */
  model: Model
  /**
   * The samplerate of the incoming audio in hertz
   */
  sampleRate: number
  /**
   * A SpkModel which allows speaker identification
   * Note: Cannot be used in conjunction with grammar right now
   */
  spkModel?: SpkModel
  /**
   * Sometimes when you want to improve recognition accuracy and when you don't need
   * to recognize large vocabulary you can specify a list of phrases to recognize. This
   * will improve recognizer speed and accuracy but might return [unk] if user said
   * something different.
   *
   * Only recognizers with lookahead models support this type of quick configuration.
   * Precompiled HCLG graph models are not supported.
   *
   * Note: Cannot be used in conjunction with spkModel right now
   */
  grammar?: string[]
}

/**
 * Create a Recognizer that will be able to transform audio streams into text using a Model
 * @see Model
 */
class Recognizer {
  protected handle: VoskRecognizer

  /**
   * Create a Recognizer that will handle speech to text recognition
   *
   * @param options            - Recognizer options
   * @param options.model      - The Model instance to use for speech to text
   * @param options.sampleRate - The samplerate of the incoming audio in hertz
   * @param options.spkModel   - A SpkModel which allows speaker identification
   * @param options.grammar    - A list of words to narrow down the words to be recognized
   */
  constructor({ model, sampleRate, spkModel, grammar }: Options) {
    if (spkModel && grammar) {
      throw new Error('spkModel and grammar cannot be used concurrently yet')
    }

    if (grammar) {
      this.handle = lib.vosk_recognizer_new_grm(
        model.getHandle(),
        sampleRate,
        JSON.stringify(grammar),
      )
      return
    }
    if (spkModel) {
      this.handle = lib.vosk_recognizer_new_spk(
        model.getHandle(),
        sampleRate,
        spkModel.getHandle(),
      )
      return
    }
    this.handle = lib.vosk_recognizer_new(model.getHandle(), sampleRate)
  }

  /**
   * Releases the model memory
   *
   * The model object is reference-counted so if some recognizer
   * depends on this model, model might still stay alive. When
   * last recognizer is released, model will be released too.
   */
  free() {
    lib.vosk_recognizer_free(this.handle)
  }

  /** Adds speaker recognition model to already created recognizer. Helps to initialize
   * speaker recognition for grammar-based recognizer.
   *
   * @param spkModel Speaker recognition model
   */
  setSpkModel(spkModel: SpkModel) {
    lib.vosk_recognizer_set_spk_model(this.handle, spkModel.getHandle())
  }

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
   * @param max_alternatives - maximum alternatives to return from recognition results
   */
  setMaxAlternatives(maxAlternatives: number) {
    return lib.vosk_recognizer_set_max_alternatives(
      this.handle,
      maxAlternatives,
    )
  }

  /**
   * Accept voice data
   *
   * accept and process new chunk of voice data
   *
   * @param data Audio data in PCM 16-bit mono format
   * @returns true If silence is occured and you can retrieve a new utterance with result method
   */
  acceptWaveform(data: Buffer) {
    return lib.vosk_recognizer_accept_waveform(this.handle, data, data.length)
  }

  /**
   * speech recognition text which is not yet finalized.
   * result may change as recognizer process more data.
   *
   * Use {@link Recognizer#partialResultObject} to retrieve the parsed PartialResult object
   *
   * @returns The partial result in JSON format
   */
  partialResult() {
    return lib.vosk_recognizer_partial_result(this.handle)
  }

  /**
   * speech recognition text which is not yet finalized.
   * result may change as recognizer process more data.
   *
   * @returns The partial results
   */
  partialResultObj(): PartialResult {
    return JSON.parse(this.partialResult())
  }

  /** Returns speech recognition result
   *
   * Use {@link Recognizer#resultObject} to retrieve the correct data type
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
  result() {
    return lib.vosk_recognizer_result(this.handle)
  }

  /**
   * Returns speech recognition results
   * @returns The results
   */
  resultObj(): Result {
    return JSON.parse(this.result())
  }

  /**
   * Returns speech recognition result. Same as result, but doesn't wait for silence
   * You usually call it in the end of the stream to get final bits of audio. It
   * flushes the feature pipeline, so all remaining audio chunks got processed.
   *
   * Use {@link Recognizer#finalResultObject} to retrieve the correct data type
   *
   * @returns Speech result in JSON format.
   */
  finalResult() {
    return lib.vosk_recognizer_final_result(this.handle)
  }

  /**
   * Returns speech recognition result. Same as result, but doesn't wait for silence
   * You usually call it in the end of the stream to get final bits of audio. It
   * flushes the feature pipeline, so all remaining audio chunks got processed.
   *
   * @returns Speech result.
   */
  finalResultObj(): Result {
    return JSON.parse(this.finalResult())
  }

  /**
   *
   * Resets current results so the recognition can continue from scratch
   */
  reset() {
    lib.vosk_recognizer_reset(this.handle)
  }
}

export default Recognizer
