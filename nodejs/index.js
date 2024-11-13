// @ts-check
'use strict'

/**
 * @module vosk
 */

const os = require('os');
const path = require('path');
/** @type {import('ffi-napi')} */
const ffi = require('ffi-napi');
/** @type {import('ref-napi')} */
const ref = require('ref-napi');

const vosk_model = ref.types.void;
const vosk_model_ptr = ref.refType(vosk_model);
const vosk_spk_model = ref.types.void;
const vosk_spk_model_ptr = ref.refType(vosk_spk_model);
const vosk_recognizer = ref.types.void;
const vosk_recognizer_ptr = ref.refType(vosk_recognizer);

/**
 * @typedef {Object} WordResult
 * @property {number} conf The confidence rate in the detection. 0 For unlikely, and 1 for totally accurate.
 * @property {number} start The start of the timeframe when the word is pronounced in seconds
 * @property {number} end The end of the timeframe when the word is pronounced in seconds
 * @property {string} word The word detected
 */

/**
 * @typedef {Object} RecognitionResults
 * @property {WordResult[]} result Details about the words that have been detected
 * @property {string} text The complete sentence that have been detected
 */

/**
 * @typedef {Object} SpeakerResults
 * @property {number[]} spk A floating vector representing speaker identity. It is usually about 128 numbers which uniquely represent speaker voice.
 * @property {number} spk_frames The number of frames used to extract speaker vector. The more frames you have the more reliable is speaker vector.
 */

/**
 * @typedef {Object} BaseRecognizerParam
 * @property {Model} model The language model to be used 
 * @property {number} sampleRate The sample rate. Most models are trained at 16kHz
 */

/**
 * @typedef {Object} GrammarRecognizerParam
 * @property {string[]} grammar The list of sentences to be recognized.
 */

/**
 * @typedef {Object} SpeakerRecognizerParam
 * @property {SpeakerModel} speakerModel The SpeakerModel that will enable speaker identification
 */

/**
 * @template {SpeakerRecognizerParam | GrammarRecognizerParam} T
 * @typedef {T extends SpeakerRecognizerParam ? SpeakerResults & RecognitionResults : RecognitionResults} Result
 */

/**
 * @typedef {Object} PartialResults
 * @property {string} partial The partial sentence that have been detected until now
 */

/** @typedef {string[]} Grammar The list of strings to be recognized */

let soname;
if (os.platform() == 'win32') {
	// Update path to load dependent dlls
	let currentPath = process.env.Path;
	let dllDirectory = path.resolve(path.join(__dirname, 'lib', 'win-x86_64'));
	process.env.Path = dllDirectory + path.delimiter + currentPath;

	soname = path.join(__dirname, 'lib', 'win-x86_64', 'libvosk.dll');
} else if (os.platform() == 'darwin') {
	soname = path.join(__dirname, 'lib', 'osx-universal', 'libvosk.dylib');
} else if (os.platform() == 'linux' && os.arch() == 'arm64') {
	soname = path.join(__dirname, 'lib', 'linux-arm64', 'libvosk.so');
} else {
	soname = path.join(__dirname, 'lib', 'linux-x86_64', 'libvosk.so');
}

const libvosk = ffi.Library(soname, {
    'vosk_set_log_level': ['void', ['int']],
    'vosk_model_new': [vosk_model_ptr, ['string']],
    'vosk_model_free': ['void', [vosk_model_ptr]],
    'vosk_spk_model_new': [vosk_spk_model_ptr, ['string']],
    'vosk_spk_model_free': ['void', [vosk_spk_model_ptr]],
    'vosk_recognizer_new': [vosk_recognizer_ptr, [vosk_model_ptr, 'float']],
    'vosk_recognizer_new_spk': [vosk_recognizer_ptr, [vosk_model_ptr, 'float', vosk_spk_model_ptr]],
    'vosk_recognizer_new_grm': [vosk_recognizer_ptr, [vosk_model_ptr, 'float', 'string']],
    'vosk_recognizer_free': ['void', [vosk_recognizer_ptr]],
    'vosk_recognizer_set_max_alternatives': ['void', [vosk_recognizer_ptr, 'int']],
    'vosk_recognizer_set_words': ['void', [vosk_recognizer_ptr, 'bool']],
    'vosk_recognizer_set_partial_words': ['void', [vosk_recognizer_ptr, 'bool']],
    'vosk_recognizer_set_spk_model': ['void', [vosk_recognizer_ptr, vosk_spk_model_ptr]],
    'vosk_recognizer_accept_waveform': ['bool', [vosk_recognizer_ptr, 'pointer', 'int']],
    'vosk_recognizer_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_final_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_partial_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_reset': ['void', [vosk_recognizer_ptr]],
});

/**
 * Set log level for Kaldi messages
 * @param {number} level The higher, the more verbose. 0 for infos and errors. Less than 0 for silence. 
 */
function setLogLevel(level) {
    libvosk.vosk_set_log_level(level);
}

/**
 * Build a Model from a model file.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
class Model {
    /**
     * Build a Model to be used with the voice recognition. Each language should have it's own Model
     * for the speech recognition to work.
     * @param {string} modelPath The abstract pathname to the model
     * @see models [models](https://alphacephei.com/vosk/models)
     */
    constructor(modelPath) {
        /**
         * Store the handle.
         * For internal use only
         * @type {unknown}
         */
        this.handle = libvosk.vosk_model_new(modelPath);
    }

    /**
     * Releases the model memory
     *
     * The model object is reference-counted so if some recognizer
     * depends on this model, model might still stay alive. When
     * last recognizer is released, model will be released too.
     */
    free() {
        libvosk.vosk_model_free(this.handle);
    }
}

/**
 * Build a Speaker Model from a speaker model file.
 * The Speaker Model enables speaker identification.
 * @see models [models](https://alphacephei.com/vosk/models)
 */
class SpeakerModel {
    /**
     * Loads speaker model data from the file and returns the model object
     *
     * @param {string} modelPath the path of the model on the filesystem
     * @see models [models](https://alphacephei.com/vosk/models)
     */
    constructor(modelPath) {
        /**
         * Store the handle.
         * For internal use only
         * @type {unknown}
         */
        this.handle = libvosk.vosk_spk_model_new(modelPath);
    }

    /**
     * Releases the model memory
     *
     * The model object is reference-counted so if some recognizer
     * depends on this model, model might still stay alive. When
     * last recognizer is released, model will be released too.
     */
    free() {
        libvosk.vosk_spk_model_free(this.handle);
    }
}

/**
 * Helper to narrow down type while using `hasOwnProperty`.
 * @see hasOwnProperty [typescript issue](https://fettblog.eu/typescript-hasownproperty/)
 * @template {Object} Obj
 * @template {PropertyKey} Key
 * @param {Obj} obj 
 * @param {Key} prop 
 * @returns {obj is Obj & Record<Key, unknown>}
 */
function hasOwnProperty(obj, prop) {
    return obj.hasOwnProperty(prop)
}

/**
 * @template T
 * @template U
 * @typedef {{ [P in Exclude<keyof T, keyof U>]?: never }} Without
 */

/**
 * @template T
 * @template U
 * @typedef {(T | U) extends object ? (Without<T, U> & U) | (Without<U, T> & T) : T | U} XOR
 */

/**
 * Create a Recognizer that will be able to transform audio streams into text using a Model.
 * @template {XOR<SpeakerRecognizerParam, Partial<GrammarRecognizerParam>>} T extra parameter
 * @see Model
 */
class Recognizer {
    /**
     * Create a Recognizer that will handle speech to text recognition.
     * @constructor
     * @param {T & BaseRecognizerParam} param The Recognizer parameters 
     *
     *  Sometimes when you want to improve recognition accuracy and when you don't need
     *  to recognize large vocabulary you can specify a list of phrases to recognize. This
     *  will improve recognizer speed and accuracy but might return [unk] if user said
     *  something different.
     *
     *  Only recognizers with lookahead models support this type of quick configuration.
     *  Precompiled HCLG graph models are not supported.
     */
    constructor(param) {
        const { model, sampleRate } = param
        // Prevent the user to receive unpredictable results
        if (hasOwnProperty(param, 'speakerModel') && hasOwnProperty(param, 'grammar')) {
            throw new Error('grammar and speakerModel cannot be used together for now.')
        }
        /**
         * Store the handle.
         * For internal use only
         * @type {unknown}
         */
        this.handle = hasOwnProperty(param, 'speakerModel')
            ? libvosk.vosk_recognizer_new_spk(model.handle, sampleRate, param.speakerModel.handle)
            : hasOwnProperty(param, 'grammar')
                ? libvosk.vosk_recognizer_new_grm(model.handle, sampleRate, JSON.stringify(param.grammar))
                : libvosk.vosk_recognizer_new(model.handle, sampleRate);
    }

    /**
     * Releases the model memory
     *
     * The model object is reference-counted so if some recognizer
     * depends on this model, model might still stay alive. When
     * last recognizer is released, model will be released too.
     */
    free() {
        libvosk.vosk_recognizer_free(this.handle);
    }

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
    setMaxAlternatives(max_alternatives) {
        libvosk.vosk_recognizer_set_max_alternatives(this.handle, max_alternatives);
    }

    /** Configures recognizer to output words with times
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
    setWords(words) {
        libvosk.vosk_recognizer_set_words(this.handle, words);
    }

    /** Same as above, but for partial results*/
    setPartialWords(partial_words) {
        libvosk.vosk_recognizer_set_partial_words(this.handle, partial_words);
    }

    /** Adds speaker recognition model to already created recognizer. Helps to initialize
     * speaker recognition for grammar-based recognizer.
     *
     * @param spk_model Speaker recognition model
     */
    setSpkModel(spk_model) {
        libvosk.vosk_recognizer_set_spk_model(this.handle, spk_model.handle);
    }

    /** 
     * Accept voice data
     *
     * accept and process new chunk of voice data
     *
     * @param {Buffer} data audio data in PCM 16-bit mono format
     * @returns true if silence is occured and you can retrieve a new utterance with result method
     */
    acceptWaveform(data) {
        return libvosk.vosk_recognizer_accept_waveform(this.handle, data, data.length);
    };

    /** 
     * Accept voice data
     *
     * accept and process new chunk of voice data
     *
     * @param {Buffer} data audio data in PCM 16-bit mono format
     * @returns true if silence is occured and you can retrieve a new utterance with result method
     */
    acceptWaveformAsync(data) {
        return new Promise((resolve, reject) => {
            libvosk.vosk_recognizer_accept_waveform.async(this.handle, data, data.length, function(err, result) {
                if (err) {
                    reject(err);
                } else {
                    resolve(result);
                }
            });
        });
    };

    /** Returns speech recognition result in a string
     *
     * @returns the result in JSON format which contains decoded line, decoded
     *          words, times in seconds and confidences. You can parse this result
     *          with any json parser
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
    resultString() {
        return libvosk.vosk_recognizer_result(this.handle);
    };

    /**
     * Returns speech recognition results
     * @returns {Result<T>} The results
     */
    result() {
        return JSON.parse(libvosk.vosk_recognizer_result(this.handle));
    };

    /**
     * speech recognition text which is not yet finalized.
     * result may change as recognizer process more data.
     * 
     * @returns {PartialResults} The partial results
     */
    partialResult() {
        return JSON.parse(libvosk.vosk_recognizer_partial_result(this.handle));
    };

    /**
     * Returns speech recognition result. Same as result, but doesn't wait for silence
     * You usually call it in the end of the stream to get final bits of audio. It
     * flushes the feature pipeline, so all remaining audio chunks got processed.
     *
     * @returns {Result<T>} speech result.
     */
    finalResult() {
        return JSON.parse(libvosk.vosk_recognizer_final_result(this.handle));
    };

    /**
     *
     * Resets current results so the recognition can continue from scratch 
     */
    reset() {
        libvosk.vosk_recognizer_reset(this.handle);
    }
}

exports.setLogLevel = setLogLevel
exports.Model = Model
exports.SpeakerModel = SpeakerModel
exports.Recognizer = Recognizer
