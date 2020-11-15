const wav = require('wav')
const fs = require('fs')

const {Readable} = require('stream')
const {Model, KaldiRecognizer, SpkModel} = require('..')

try {
    fs.accessSync('model', fs.constants.R_OK)
} catch (err) {
    console.error("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as 'model' in the current folder.")
    process.exit(1)
}

try {
    fs.accessSync('model-spk', fs.constants.R_OK)
} catch (err) {
    console.error("Please download the speaker model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as 'model-spk' in the current folder.")
    process.exit(1)
}

const wfStream = fs.createReadStream('test.wav', { highWaterMark: 4096 })
const wfReader = new wav.Reader()

const model = new Model('model')
const spkModel = new SpkModel('model-spk')

const spk_sig = [-0.56648, 0.030579, 1.730239, 0.239899, -1.194183,
0.251954, 0.540388, -0.971872, -0.020963, 0.085036, 0.563973, -0.019682,
-0.597381, 1.094719, -0.566738, 0.29819, 0.171165, 0.370341, -0.033539,
-0.09757, 1.228286, 0.485949, 0.427826, 0.147762, -0.015112, 0.599513,
-2.040655, -0.490882, 0.440161, -0.072991, 0.835955, -0.496124, 0.952978,
0.85356, -1.096116, 0.107764, -0.385486, 1.410305, 0.609147, -0.457014,
-1.542864, 0.343669, 0.171913, -0.627281, -1.281781, -1.134276,
-0.639895, 1.190183, -0.700537, 1.063457, 0.206946, 0.342198, -1.165625,
1.475955, -0.089007, -2.555155, 0.551438, -0.212736, 1.025625, -1.631965,
-0.716256, -1.295995, 1.554956, -1.866009, -1.010782, -1.43231, 0.109027,
2.123925, 1.703283, -0.784997, 2.730568, 0.755113, 0.0617, 0.128955,
-0.054047, 1.359119, -0.611666, -1.105754, -0.631353, 0.052109, 0.729386,
-0.769876, 1.250235, -1.463298, 0.648176, -0.73239, -0.385239,
-1.661856, 0.602106, -0.45567, -1.438431, -0.836673, 0.033557, 0.373597,
-1.343341, -0.181095, 0.237287, -0.522005, -1.722836, 0.932333,
-0.092861, -0.219254, 0.476182, 1.033803, -1.633563, -0.874341, 1.039064,
-1.758573, -0.838422, -0.324336, -0.924634, 1.962594, 2.152814, 1.2521,
-0.46172, -1.50271, 1.685691, 0.403097, -0.819042, 0.866403, -0.591716,
-0.578645, -0.553839, 0.381861, -1.051647, -1.477578, 0.524005, 0.925245]

function dotp(x, y) {
    function dotp_sum(a, b) {
        return a + b
    }
    function dotp_times(a, i) {
        return x[i] * y[i]
    }
    return x.map(dotp_times).reduce(dotp_sum, 0)
}

function cosineSimilarity(A, B) {
    var similarity =
        dotp(A, B) / (Math.sqrt(dotp(A, A)) * Math.sqrt(dotp(B, B)))
        return similarity
}

function cosine_dist(x, y) {
    return 1 - cosineSimilarity(x, y)
}

wfReader.on('format', async ({ audioFormat, sampleRate, channels }) => {
    if (audioFormat != 1 || channels != 1) {
        console.error('Audio file must be WAV format mono PCM.')
        process.exit(1)
    }
    const rec = new KaldiRecognizer(model, spkModel, sampleRate)
    for await (const data of new Readable().wrap(wfReader)) {
        const endOfSpeech = await rec.AcceptWaveform(data)
        if (endOfSpeech) {
            res = await JSON.parse(rec.Result());
            console.log(res)
            console.log('X-vector:', JSON.stringify(res['spk']))
            console.log('Speaker distance:', cosine_dist(spk_sig, res['spk']))
        } else {
            console.log(await rec.PartialResult())
        }
    }
    res = await JSON.parse(rec.FinalResult());
    console.log(res)
    console.log('X-vector:', JSON.stringify(res['spk']))
    console.log('Speaker distance:', cosine_dist(spk_sig, res['spk']))
})

wfStream.pipe(wfReader)
