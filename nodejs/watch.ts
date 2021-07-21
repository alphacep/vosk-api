import {
  setLogLevel,
  // Model,
  // SpkModel,
  Recognizer,
  getModelAsync,
  getSpkModelAsync,
} from './src/index'

import fs from 'fs'
import { Readable } from 'stream'
import wav from 'wav'

const main = async () => {
  setLogLevel(2)
  // Instead of loading the model in the main thread like this:
  // const model = new Model('model')
  // We can load it in a different thread like:
  const model = await getModelAsync('model')

  // Same for the speaker model
  // const spkModel = new SpkModel('spk_model')
  const spkModel = await getSpkModelAsync('spk_model')

  const rec = new Recognizer({
    model,
    sampleRate: 16000,
    spkModel,
  })
  // rec.setMaxAlternatives(2)
  rec.setWords(true)

  // To narrow down the possible words to appear in the result
  // const rec = new Recognizer(model, 16000.0, [
  //   'oh one two three four five six seven eight nine zero',
  //   '[unk]',
  // ])

  const wfStream = fs.createReadStream('test.wav', { highWaterMark: 4096 })
  const wfReader = new wav.Reader()

  wfReader.on('format', async ({ audioFormat, /* sampleRate, */ channels }) => {
    if (audioFormat != 1 || channels != 1) {
      console.error('Audio file must be WAV format mono PCM.')
      process.exit(1)
    }
    for await (const data of new Readable().wrap(wfReader)) {
      const end_of_speech = await rec.acceptWaveformAsync(data)
      if (end_of_speech) {
        console.log('end_of_speech', rec.resultObj())
      } else {
        console.log('partial', rec.partialResultObj())
      }
    }
    console.log('final', rec.finalResultObj())

    rec.free()
    model.free()
    spkModel.free()
  })

  wfStream.pipe(wfReader)
}

main()
