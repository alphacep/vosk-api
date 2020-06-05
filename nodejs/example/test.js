#!/usr/bin/env node

const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

const { Model, KaldiRecognizer } = require("..");

try {
    fs.accessSync("model", fs.constants.R_OK);
} catch(err) {
    console.error("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as 'model' in the current folder.");
    process.exit(1);
}

const wfStream = fs.createReadStream("test.wav", {'highWaterMark': 4096});
const wfReader = new wav.Reader();

const model = new Model("model");

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
    if (audioFormat != 1 || channels != 1) {
        console.error("Audio file must be WAV format mono PCM.");
        process.exit(1);
    }
    const rec = new KaldiRecognizer(model, sampleRate);
    for await (const data of new Readable().wrap(wfReader)) {
        const result = await rec.AcceptWaveform(data);
        if (result != 0) {
           console.log(await rec.Result());
        } else {
           console.log(await rec.PartialResult());
        }
    }
    console.log(await rec.FinalResult());
});

wfStream.pipe(wfReader);
