var vosk = require('..')

const fs = require("fs");
var mic = require("mic");

MODEL_PATH = "model"
SAMPLE_RATE = 16000

if (!fs.existsSync(MODEL_PATH)) {
    console.log("Please download the model from https://alphacephei.com/vosk/models and unpack as " + MODEL_PATH + " in the current folder.")
    process.exit()
}

vosk.setLogLevel(0);
const model = new vosk.Model(MODEL_PATH);
const rec = new vosk.Recognizer({model: model, sampleRate: SAMPLE_RATE});

var micInstance = mic({
    rate: String(SAMPLE_RATE),
    channels: '1',
    debug: false
});

var micInputStream = micInstance.getAudioStream();
micInstance.start();

micInputStream.on('data', data => {
    if (rec.acceptWaveform(data))
        console.log(rec.result());
    else
        console.log(rec.partialResult());
});

process.on('SIGINT', function() {
    console.log(rec.finalResult());
    console.log("\nDone");
    rec.free();
    model.free();
});
