import * as vosk from "../mod.ts";
import fs from "node:fs";
import process from "node:process";

import { spawn } from "node:child_process";
import { stringifySync } from "npm:subtitle";

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

vosk.setLogLevel(-1);
const model = new vosk.Model(MODEL_PATH);
const rec = new vosk.Recognizer({ model: model, sampleRate: SAMPLE_RATE });
rec.setWords(true);

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

const WORDS_PER_LINE = 7;
const subs = [];
const results = [];
ffmpeg_run.stdout.on("data", (stdout) => {
  if (rec.acceptWaveform(stdout)) {
    results.push(rec.result());
  }
  results.push(rec.finalResult());
});

ffmpeg_run.on("exit", () => {
  rec.free();
  model.free();
  results.forEach((element) => {
    if (!Object.hasOwn(element, "result")) {
      return;
    }
    const words = element.result;
    if (words.length == 1) {
      subs.push({
        type: "cue",
        data: {
          start: words[0].start * 1000,
          end: words[0].end * 1000,
          text: words[0].word,
        },
      });
      return;
    }
    const start_index = 0;
    let text = words[0].word + " ";
    for (let i = 1; i < words.length; i++) {
      text += words[i].word + " ";
      if (i % WORDS_PER_LINE == 0) {
        subs.push({
          type: "cue",
          data: {
            start: words[start_index].start * 1000,
            end: words[i].end * 1000,
            text: text.slice(0, text.length - 1),
          },
        });

        text = "";
      }
    }
    if (start_index != words.length - 1) {
      subs.push({
        type: "cue",
        data: {
          start: words[start_index].start * 1000,
          end: words[words.length - 1].end * 1000,
          text: text,
        },
      });
    }
  });
  console.log(stringifySync(subs, { format: "SRT" }));
});
