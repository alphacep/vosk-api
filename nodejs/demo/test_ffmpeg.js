var vosk = require('..')

const fs = require("fs");
const { spawn } = require("child_process");
const Stream = require('stream');

MODEL_PATH = "model"
FILE_NAME = "test.wav"
SAMPLE_RATE = 16000 

if (!(fs.existsSync(MODEL_PATH) && fs.lstatSync(MODEL_PATH).isDirectory())){
    console.log("Please download the model from https://alphacephei.com/vosk/models and unpack as " + MODEL_PATH + " in the current folder.")
    process.exit()
}

if (process.argv.length > 2)
    FILE_NAME = process.argv[2]

vosk.setLogLevel(0);
const model = new vosk.Model(MODEL_PATH);
const rec = new vosk.Recognizer({model: model, sampleRate: SAMPLE_RATE});

const ffmpeg_run = spawn('ffmpeg', ['-loglevel', 'quiet', '-i', FILE_NAME,
                         '-ar', String(SAMPLE_RATE) , '-ac', '1',
                         '-f', 's16le', '-']);

ffmpeg_run.stdout.on('data', (stdout) => {
    const wave_stream = Stream.Readable.from(stdout)
    while (true){
        const data = wave_stream.read(4000)
        if (data == null)
            break;
        if (rec.acceptWaveform(data))
            console.log(rec.result());
        else
            console.log(rec.partialResult());
    }
    console.log(rec.finalResult());
});
