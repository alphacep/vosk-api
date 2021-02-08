var ffi = require('ffi-napi');
var ref = require('ref-napi');

const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

const vosk_model = ref.types.void;
const vosk_model_ptr = ref.refType(vosk_model);
const vosk_spk_model = ref.types.void;
const vosk_spk_model_ptr = ref.refType(vosk_spk_model);
const vosk_recognizer = ref.types.void;
const vosk_recognizer_ptr = ref.refType(vosk_recognizer);
 
const libvosk = ffi.Library('./libvosk', {
  'vosk_set_log_level': [ 'void', [ 'int' ] ],
  'vosk_model_new': [ vosk_model_ptr, [ 'string' ] ],
  'vosk_model_free': [ 'void', [ vosk_model_ptr ] ],
  'vosk_recognizer_new': [ vosk_recognizer_ptr, [ vosk_model_ptr, 'float' ] ],
  'vosk_recognizer_free': [ 'void', [ vosk_recognizer_ptr ] ],
  'vosk_recognizer_accept_waveform': [ 'bool', [ vosk_recognizer_ptr, 'pointer', 'int' ] ],
  'vosk_recognizer_result': ['string', [vosk_recognizer_ptr ] ],
  'vosk_recognizer_final_result': ['string', [vosk_recognizer_ptr ] ],
});

libvosk.vosk_set_log_level(0);
const model = libvosk.vosk_model_new("model");
const rec = libvosk.vosk_recognizer_new(model, 16000.0);

const wfStream = fs.createReadStream("test.wav", {'highWaterMark': 4096});
const wfReader = new wav.Reader();

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
    if (audioFormat != 1 || channels != 1) {
        console.error("Audio file must be WAV format mono PCM.");
        process.exit(1);
    }
    for await (const data of new Readable().wrap(wfReader)) {
        const result = libvosk.vosk_recognizer_accept_waveform(rec, data, data.length);
        if (result) {
              console.log(libvosk.vosk_recognizer_result(rec));
        }
    }
    console.log(libvosk.vosk_recognizer_final_result(rec));
    libvosk.vosk_recognizer_free(rec);
    libvosk.vosk_model_free(model);
});

wfStream.pipe(wfReader);
