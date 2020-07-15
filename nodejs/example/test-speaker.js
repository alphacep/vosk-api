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

const spk_sig = [4.658117, 1.277387, 3.346158, -1.473036, -2.15727,
2.461757, 3.76756, -1.241252, 2.333765, 0.642588, -2.848165, 1.229534,
3.907015, 1.726496, -1.188692, 1.16322, -0.668811, -0.623309, 4.628018,
0.407197, 0.089955, 0.920438, 1.47237, -0.311365, -0.437051, -0.531738,
-1.591781, 3.095415, 0.439524, -0.274787, 4.03165, 2.665864, 4.815553,
1.581063, 1.078242, 5.017717, -0.089395, -3.123428, 5.34038, 0.456982,
2.465727, 2.131833, 4.056272, 1.178392, -2.075712, -1.568503, 0.847139,
0.409214, 1.84727, 0.986758, 4.222116, 2.235512, 1.369377, 4.283126,
2.278125, -1.467577, -0.999971, 3.070041, 1.462214, 0.423204, 2.143578,
0.567174, -2.294655, 1.864723, 4.307356, 2.610872, -1.238721, 0.551861,
2.861954, 0.59613, -0.715396, -1.395357, 2.706177, -2.004444, 2.055255,
0.458283, 1.231968, 3.48234, 2.993858, 0.402819, 0.940885, 0.360162,
-2.173674, -2.504609, 0.329541, 3.653913, 3.638025, -1.406409, 2.14059,
1.662765, -0.991323, 0.770921, 0.010094, 3.775469, 1.847511, 2.074432,
-1.928593, 0.807414, 2.964505, 0.128597, 1.297962, 2.645227, 0.136405,
-2.543087, 0.932246, 2.405783, -2.122267, 3.044013, 0.486728, 4.395338,
0.474267, 0.781297, 1.694144, -0.831078, -0.462362, -0.964715, 3.187863,
6.008708, 1.725954, 3.667886, -1.467623, 3.370667, 2.72555, -0.796541,
2.416543, 0.675401, -0.737634, -1.709676]

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
