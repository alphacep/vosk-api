const vosk = require('..');

const fs = require("fs");
const { Readable } = require("stream");
const wav = require("wav");

const model = new vosk.Model('model');
const speakerModel = new vosk.SpeakerModel('model-spk');

const wfStream = fs.createReadStream('test.wav', { highWaterMark: 4096 });
const wfReader = new wav.Reader();
const wfReadable = new Readable().wrap(wfReader);

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
  if (audioFormat != 1 || channels != 1) {
      console.error('Audio file must be WAV format mono PCM.');
      process.exit(1);
  }
  const rec = new vosk.Recognizer({ model: model,
                                    speakerModel: speakerModel,
                                    sampleRate: sampleRate });
  for await (const data of wfReadable) {
      const end_of_speech = rec.acceptWaveform(data);
      if (end_of_speech) {
        console.log(rec.finalResult());
      }
  }
  console.log(rec.finalResult());
  rec.free();
});
wfStream.pipe(wfReader).on('finish', function (err) {
    model.free();
    speakerModel.free();
});
