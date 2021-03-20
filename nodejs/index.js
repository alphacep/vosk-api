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
 * @property {number} conf The confidence rate in the detection
 * @property {number} start The start of the timeframe when the word is pronounced
 * @property {number} end The end of the timeframe when the word is pronounced
 * @property {string} word The word detected
 */

/**
 * @typedef {Object} RecognitionResults
 * @property {WordResult[]} result Details about the words that have been detected
 * @property {string} text The complete sentence that have been detected
 */

/**
 * @typedef {Object} PartialResults
 * @property {string} partial The partial sentence that have been detected until now
 */

var soname;
if (os.platform == 'win32') {
    soname = path.join(__dirname, "lib", "win-x86_64", "libvosk.dll")
} else if (os.platform == 'darwin') {
    soname = path.join(__dirname, "lib", "osx-x86_64", "libvosk.dylib")
} else {
    soname = path.join(__dirname, "lib", "linux-x86_64", "libvosk.so")
}

const libvosk = ffi.Library(soname, {
    'vosk_set_log_level': ['void', ['int']],
    'vosk_model_new': [vosk_model_ptr, ['string']],
    'vosk_model_free': ['void', [vosk_model_ptr]],
    'vosk_recognizer_new': [vosk_recognizer_ptr, [vosk_model_ptr, 'float']],
    'vosk_recognizer_free': ['void', [vosk_recognizer_ptr]],
    'vosk_recognizer_accept_waveform': ['bool', [vosk_recognizer_ptr, 'pointer', 'int']],
    'vosk_recognizer_result': ['string', [vosk_recognizer_ptr]],
    'vosk_recognizer_final_result': ['string', [vosk_recognizer_ptr]],
});

/**
 * Set log level for Kaldi messages
 * @param {number} level The higher, the more verbose. 0 for infos and errors. Less than 0 for silence. 
 */
function setLogLevel(level) {
    libvosk.vosk_set_log_level(level);
}

class Model {
    /**
     * Build a Model to be used with the voice recognition. Each language should have it's own Model
     * for the speech recognition to work.
     * @param {string} model_path The abstract pathname to the model
     */
    constructor(model_path) {
        this.handle = libvosk.vosk_model_new(model_path);
    }

    /**
     * Return the handle.
     * For internal use only
     * @returns {unknown} A reference to the internal representation of the Model
     */
     getHandle() {
        return this.handle
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

class Recognizer {
    /**
     * Create a Recognizer that will handle speech to text recognition.
     * @param {Model} model The language model to be used 
     * @param {number} sample_rate The sample rate. Most models are trained at 16kHz
     */
    constructor(model, sample_rate) {
        this.handle = libvosk.vosk_recognizer_new(model.getHandle(), sample_rate);
    }

    /**
     * Releases the model memory
     *
     * The model object is reference-counted so if some recognizer
     * depends on this model, model might still stay alive. When
     * last recognizer is released, model will be released too.
     */
    free () {
        libvosk.vosk_recognizer_free(this.handle);
    }

    /** 
     * Accept voice data
     *
     * accept and process new chunk of voice data
     *
     * @param data - audio data in PCM 16-bit mono format
     * @returns true if silence is occured and you can retrieve a new utterance with result method
     */
    acceptWaveform (data) {
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
    result () {
        return libvosk.vosk_recognizer_result(this.handle);
    };

    /**
     * Returns speech recognition results
     * @returns {RecognitionResults} The results
     */
    resultObject () {
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
    finalResult () {
        return libvosk.vosk_recognizer_final_result(this.handle);
    };

    /** 
     * Returns speech recognition result. Same as result, but doesn't wait for silence
     * You usually call it in the end of the stream to get final bits of audio. It
     * flushes the feature pipeline, so all remaining audio chunks got processed.
     *
     * @returns {RecognitionResults} speech result.
     */
    finalResultObject () {
        return JSON.parse(libvosk.vosk_recognizer_final_result(this.handle));
    };
}

exports.setLogLevel = setLogLevel
exports.Model = Model
exports.Recognizer = Recognizer
