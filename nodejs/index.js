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
} else {
    soname = path.join(__dirname, "lib", "linux-x86_64", "libvosk.so")
}

const libvosk = ffi.Library(soname, {
  'vosk_set_log_level': [ 'void', [ 'int' ] ],
  'vosk_model_new': [ vosk_model_ptr, [ 'string' ] ],
  'vosk_model_free': [ 'void', [ vosk_model_ptr ] ],
  'vosk_recognizer_new': [ vosk_recognizer_ptr, [ vosk_model_ptr, 'float' ] ],
  'vosk_recognizer_free': [ 'void', [ vosk_recognizer_ptr ] ],
  'vosk_recognizer_accept_waveform': [ 'bool', [ vosk_recognizer_ptr, 'pointer', 'int' ] ],
  'vosk_recognizer_result': ['string', [vosk_recognizer_ptr ] ],
  'vosk_recognizer_final_result': ['string', [vosk_recognizer_ptr ] ],
});

function setLogLevel(level) {
    libvosk.vosk_set_log_level(level);
}

function Model(model_path) {

    this.handle = libvosk.vosk_model_new(model_path);

    this.free = function() {
        libvosk.vosk_model_free(this.handle);
    }

    this.getHandle = function() {
        return this.handle;
    }
}


function Recognizer(model, sample_rate) {
    this.handle = libvosk.vosk_recognizer_new(model.getHandle(), sample_rate);

    this.free = function() {
        libvosk.vosk_recognizer_free(this.handle);
    }

    this.acceptWaveform = function(data) {
       return libvosk.vosk_recognizer_accept_waveform(this.handle, data, data.length);
    }

    this.result = function() {
        return libvosk.vosk_recognizer_result(this.handle);
    }

    this.partialResult = function() {
        return libvosk.vosk_recognizer_partial_result(this.handle);
    }

    this.finalResult = function() {
        return libvosk.vosk_recognizer_final_result(this.handle);
    }
}

exports.setLogLevel = setLogLevel
exports.Model = Model
exports.Recognizer = Recognizer
