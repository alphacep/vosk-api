'use strict'

const os = require('os');
const path = require('path');
const ffi = require('ffi-napi');
const ref = require('ref-napi');

const vosk_model = ref.types.void;
const vosk_model_ptr = ref.refType(vosk_model);
const vosk_spk_model = ref.types.void;
const vosk_spk_model_ptr = ref.refType(vosk_spk_model);
const vosk_recognizer = ref.types.void;
const vosk_recognizer_ptr = ref.refType(vosk_recognizer);

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
 * Set the level of details of logs
 * What are the possible values?
 * @param {number} level No idea. The higher the most detailed? Or is it the opposite?
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
     * Probably just needed internally I guess?
     * @returns {unknown} A handle... What is it?
     */
     getHandle() {
        return this.handle
    }

    /** Free up the memory */
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

    /** Free up the memory */
    free () {
        libvosk.vosk_recognizer_free(this.handle);
    }

    /**
     * Well, for sure, it does something with some data. I probably got that right.
     * @param {unkown} data something
     * @returns {unkown} something else
     */
    acceptWaveform (data) {
        return libvosk.vosk_recognizer_accept_waveform(this.handle, data, data.length);
    };

    /**
     * Retrieves the results, but I have no idea what shape to expect
     * @returns {unkown} The results I guess?
     */
    result () {
        return libvosk.vosk_recognizer_result(this.handle);
    };

    /**
     * Maybe I'll get some letters from the actual sentence, for those who want to play the hangman game?
     * @returns {unkown} Partial results?
     */
    partialResult = function () {
        return libvosk.vosk_recognizer_partial_result(this.handle);
    };

    /**
     * That definitely looks definitive.
     * @returns {unkown} Yet another result
     */
    finalResult () {
        return libvosk.vosk_recognizer_final_result(this.handle);
    };
}

exports.setLogLevel = setLogLevel
exports.Model = Model
exports.Recognizer = Recognizer
