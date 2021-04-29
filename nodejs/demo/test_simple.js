var vosk = require('..')

const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

MODEL_PATH = "model"

if (!(fs.existsSync(MODEL_PATH) && fs.lstatSync(MODEL_PATH).isDirectory())){
    console.log("Please download the model from https://alphacephei.com/vosk/models and unpack as " + MODEL_PATH + " in the current folder.")
    process.exit()
}

vosk.setLogLevel(0);
const model = new vosk.Model(MODEL_PATH);

const wfStream = fs.createReadStream("test.wav", {'highWaterMark': 4096});
const wfReader = new wav.Reader();
const wfReadable = new Readable().wrap(wfReader);

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
    if (audioFormat != 1 || channels != 1) {
        console.error("Audio file must be WAV format mono PCM.");
        process.exit(1);
    }
    const rec = new vosk.Recognizer({model: model, sampleRate: sampleRate});
    for await (const data of wfReadable) {
        const end_of_speech = rec.acceptWaveform(data);
        if (end_of_speech) {
              console.log(rec.result());
        }
    }
    console.log(rec.finalResult(rec));
    rec.free();
});
wfStream.pipe(wfReader).on('finish', function (err) {
    model.free();
});
