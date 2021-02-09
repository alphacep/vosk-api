var vosk = require('..')

const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

vosk.setLogLevel(0);
const model = new vosk.Model("model");
const rec = new vosk.Recognizer(model, 16000.0);

const wfStream = fs.createReadStream("test.wav", {'highWaterMark': 4096});
const wfReader = new wav.Reader();

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
    if (audioFormat != 1 || channels != 1) {
        console.error("Audio file must be WAV format mono PCM.");
        process.exit(1);
    }
    for await (const data of new Readable().wrap(wfReader)) {
        const end_of_speech = rec.acceptWaveform(data);
        if (end_of_speech) {
              console.log(rec.result());
        }
    }
    console.log(rec.finalResult(rec));
    rec.free();
    model.free();
});

wfStream.pipe(wfReader);
