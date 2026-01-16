const vosk = require('..');
const fs = require('fs');
const { spawn } = require('child_process');
const { platform } = require('os');

const MODEL_PATH = 'model';
const SAMPLE_RATE = 16000;
const soxInputPlatformDic = {
  win32: 'waveaudio',
  linux: 'pulseaudio',
  darwin: 'coreaudio',
};

if (!fs.existsSync(MODEL_PATH)) {
  console.log(
    'Please download the model from https://alphacephei.com/vosk/models and unpack as ' +
      MODEL_PATH +
      ' in the current folder.',
  );
  process.exit();
}

vosk.setLogLevel(1);
const model = new vosk.Model(MODEL_PATH);
const rec = new vosk.Recognizer({ model: model, sampleRate: SAMPLE_RATE });

// Install Sox before using this example: https://sourceforge.net/projects/sox/files/sox/
const soxProcess = spawn(`sox`, [
  '-b',
  '16',
  '--endian',
  'little',
  '-c',
  '1',
  '-r',
  '16k',
  '-e',
  'signed-integer',
  '-t',
  soxInputPlatformDic[platform],
  'default',
  '-t',
  'wav',
  '-',
]);

// Pass audio (data) into the Vosk API
soxProcess.stdout.on('data', data => {
  if (rec.acceptWaveform(data)) console.log(rec.result());
  else console.log(rec.partialResult());
});

// Handle errors of Sox instance
soxProcess.on('error', error => {
  console.log('Error executing Sox: ', error.message);
});

process.on('SIGINT', function () {
  console.log('\nStopping');
  soxProcess.kill('SIGTERM');
});
