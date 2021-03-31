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
 * @property {number[]} spk Speaker vectors... Whatever that might mean 
 * @property {number} spk_frames Speaker frames... I suppose
 */

/**
 * @template {string[] | SpeakerModel | undefined} T
 * @typedef {T extends SpeakerModel ? SpeakerResults & RecognitionResults : RecognitionResults} Result
 */

/**
 * @typedef {Object} PartialResults
 * @property {string} partial The partial sentence that have been detected until now
 */

/** @typedef {string[]} Grammar The list of strings to be recognized */

var soname;
if (os.platform() == 'win32') {
    soname = path.join(__dirname, "lib", "win-x86_64", "libvosk.dll")
} else if (os.platform() == 'darwin') {
    soname = path.join(__dirname, "lib", "osx-x86_64", "libvosk.dylib")
} else {
    soname = path.join(__dirname, "lib", "linux-x86_64", "libvosk.so")
}

const libvosk = ffi.Library(soname, {
    'vosk_set_log_level': ['void', ['int']],
    'vosk_model_new': [vosk_model_ptr, ['string']],
    'vosk_model_free': ['void', [vosk_model_ptr]],
    'vosk_spk_model_new': [vosk_spk_model_ptr, ['string']],
    'vosk_spk_model_free': ['void', [vosk_spk_model_ptr]],
    'vosk_recognizer_new': [vosk_recognizer_ptr, [vosk_model_ptr, 'float']],
    'vosk_recognizer_new_spk': [vosk_recognizer_ptr, [vosk_model_ptr, vosk_spk_model_ptr, 'float']],
    'vosk_recognizer_new_grm': [vosk_recognizer_ptr, [vosk_model_ptr, 'float', 'string']],
    'vosk_recognizer_free': ['void', [vosk_recognizer_ptr]],
    'vosk_recognizer_accept_waveform': ['bool', [vosk_recognizer_ptr, 'pointer', 'int']],
    'vosk_recognizer_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_final_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_partial_result': ['string', [vosk_recognizer_ptr]],
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
 * Create a Recognizer that will be able to transform audio streams into text using a Model.
 * @template {string[] | SpeakerModel | undefined} T extra parameter
 * @see Model
 */
class Recognizer {
    /**
     * Create a Recognizer that will handle speech to text recognition.
     * @constructor
     * @param {Model} model The language model to be used 
     * @param {number} sampleRate The sample rate. Most models are trained at 16kHz
     * @param {T=} grammarOrModel The SpeakerModel that will enable speaker identification, or the list of phrases to be recognized.
     *
     *  Sometimes when you want to improve recognition accuracy and when you don't need
     *  to recognize large vocabulary you can specify a list of phrases to recognize. This
     *  will improve recognizer speed and accuracy but might return [unk] if user said
     *  something different.
     *
     *  Only recognizers with lookahead models support this type of quick configuration.
     *  Precompiled HCLG graph models are not supported.
     */
    constructor(model, sampleRate, grammarOrModel) {
        /**
         * Store the handle.
         * For internal use only
         * @type {unknown}
         */
        this.handle = grammarOrModel instanceof SpeakerModel
            ? libvosk.vosk_recognizer_new_spk(model.handle, grammarOrModel.handle, sampleRate)
            : grammarOrModel
                ? libvosk.vosk_recognizer_new(model.handle, sampleRate)
                : libvosk.vosk_recognizer_new_grm(model.handle, sampleRate, JSON.stringify(grammarOrModel));
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

    /** Returns speech recognition result
     *
     * @deprecated Use {@link Recognizer#resultObject} to retrieve the correct data type
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
        return libvosk.vosk_recognizer_result(this.handle);
    };

    /**
     * Returns speech recognition results
     * @returns {Result<T>} The results
     */
    resultObject() {
        return JSON.parse(libvosk.vosk_recognizer_result(this.handle));
    };

    /**
     * speech recognition text which is not yet finalized.
     * result may change as recognizer process more data.
     * 
     * @deprecated Use {@link Recognizer#partialResultObject} to retrieve the correct data type
     * @returns {string} The partial result in JSON format
     */
    partialResult = function () {
        return libvosk.vosk_recognizer_partial_result(this.handle);
    };

    /**
     * speech recognition text which is not yet finalized.
     * result may change as recognizer process more data.
     * 
     * @returns {PartialResults} The partial results
     */
    partialResultObject = function () {
        return JSON.parse(libvosk.vosk_recognizer_partial_result(this.handle));
    };

    /** 
     * Returns speech recognition result. Same as result, but doesn't wait for silence
     * You usually call it in the end of the stream to get final bits of audio. It
     * flushes the feature pipeline, so all remaining audio chunks got processed.
     *
     * @deprecated Use {@link Recognizer#finalResultObject} to retrieve the correct data type
     * @returns {string} speech result in JSON format.
     */
    finalResult() {
        return libvosk.vosk_recognizer_final_result(this.handle);
    };

    /** 
     * Returns speech recognition result. Same as result, but doesn't wait for silence
     * You usually call it in the end of the stream to get final bits of audio. It
     * flushes the feature pipeline, so all remaining audio chunks got processed.
     *
     * @returns {Result<T>} speech result.
     */
    finalResultObject() {
        return JSON.parse(libvosk.vosk_recognizer_final_result(this.handle));
    };
}

exports.setLogLevel = setLogLevel
exports.Model = Model
exports.SpeakerModel = SpeakerModel
exports.Recognizer = Recognizer
