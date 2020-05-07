#!/usr/bin/python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import ffmpeg

SetLogLevel(0)

if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as 'model' in the current folder.")
    exit (1)

sample_rate=16000
model = Model("model")
rec = KaldiRecognizer(model, sample_rate)

process = (
    ffmpeg
    .input(sys.argv[1])
    .output('-', format='s16le', acodec='pcm_s16le', ac=1, ar=sample_rate,  loglevel='quiet')
    .run_async(pipe_stdout=True)
)

while True:
    data = process.stdout.read(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(rec.Result())
    else:
        print(rec.PartialResult())

print(rec.FinalResult())
