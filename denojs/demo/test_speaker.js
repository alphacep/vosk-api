import * as vosk from "../mod.ts";
import wav from "npm:wav";
import fs from "node:fs";
import process from "node:process";
import { Readable } from "node:stream";

const MODEL_PATH = "model";
const SPEAKER_MODEL_PATH = "model-spk";
const FILE_NAME = "test.wav";

if (!fs.existsSync(MODEL_PATH)) {
  console.log(
    "Please download the model from https://alphacephei.com/vosk/models and unpack as " +
      MODEL_PATH + " in the current folder.",
  );
  process.exit();
}

if (!fs.existsSync(SPEAKER_MODEL_PATH)) {
  console.log(
    "Please download the speaker model from https://alphacephei.com/vosk/models and unpack as " +
      SPEAKER_MODEL_PATH + " in the current folder.",
  );
  process.exit();
}

if (process.argv.length > 2) {
  FILE_NAME = process.argv[2];
}

const model = new vosk.Model(MODEL_PATH);
const speakerModel = new vosk.SpeakerModel(SPEAKER_MODEL_PATH);

const wfReader = new wav.Reader();
const wfReadable = new Readable().wrap(wfReader);

wfReader.on("format", async ({ audioFormat, sampleRate, channels }) => {
  if (audioFormat != 1 || channels != 1) {
    console.error("Audio file must be WAV format mono PCM.");
    process.exit(1);
  }
  //    const rec = new vosk.Recognizer({ model: model,
  //                                      speakerModel: speakerModel,
  //                                      sampleRate: sampleRate });
  const rec = new vosk.Recognizer({ model: model, sampleRate: sampleRate });
  rec.setSpkModel(speakerModel);
  for await (const data of wfReadable) {
    const end_of_speech = rec.acceptWaveform(data);
    if (end_of_speech) {
      console.log(rec.finalResult());
    }
  }
  console.log(rec.finalResult());
  rec.free();
});

fs.createReadStream(FILE_NAME, { highWaterMark: 4096 }).pipe(wfReader).on(
  "finish",
  function () {
    model.free();
    speakerModel.free();
  },
);
