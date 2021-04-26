var vosk = require('..')

const async = require("async");
const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

// Process file 4 times in parallel with a single model
files = ["test.wav", "test.wav", "test.wav", "test.wav"]
const model = new vosk.Model("model");

async.filter(files, function(filePath, callback) {
    const wfStream = fs.createReadStream("test.wav", {'highWaterMark': 4096});
    const wfReader = new wav.Reader();
    const wfReadable = new Readable().wrap(wfReader);

    wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
        const rec = new vosk.Recognizer({model: model, sampleRate: sampleRate});
        if (audioFormat != 1 || channels != 1) {
            console.error("Audio file must be WAV format mono PCM.");
            process.exit(1);
        }
        for await (const data of wfReadable) {
            const end_of_speech = await rec.acceptWaveformAsync(data);
            if (end_of_speech) {
                  console.log(rec.result());
            }
        }
        console.log(rec.finalResult(rec));
        rec.free();
        // Signal we are done without errors
        callback(null, true);
    });
    wfStream.pipe(wfReader);
}, function(err, results) {
    model.free();
    console.log("Done!!!!!");
});
