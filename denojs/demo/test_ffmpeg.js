import * as vosk from "../mod.ts";
import fs from "node:fs";
import { spawn } from "node:child_process";
import process from "node:process";

const MODEL_PATH = "model";
const FILE_NAME = "test.wav";
const SAMPLE_RATE = 16000;
const BUFFER_SIZE = 4000;

if (!fs.existsSync(MODEL_PATH)) {
  console.log(
    "Please download the model from https://alphacephei.com/vosk/models and unpack as " +
      MODEL_PATH + " in the current folder.",
  );
  process.exit();
}

if (process.argv.length > 2) {
  FILE_NAME = process.argv[2];
}

vosk.setLogLevel(0);
const model = new vosk.Model(MODEL_PATH);
const rec = new vosk.Recognizer({ model: model, sampleRate: SAMPLE_RATE });

const ffmpeg_run = spawn("ffmpeg", [
  "-loglevel",
  "quiet",
  "-i",
  FILE_NAME,
  "-ar",
  String(SAMPLE_RATE),
  "-ac",
  "1",
  "-f",
  "s16le",
  "-bufsize",
  String(BUFFER_SIZE),
  "-",
]);

ffmpeg_run.stdout.on("data", (stdout) => {
  if (rec.acceptWaveform(stdout)) {
    console.log(rec.result());
  } else {
    console.log(rec.partialResult());
  }
  console.log(rec.finalResult());
});
