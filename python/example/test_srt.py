#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import subprocess

SetLogLevel(-1)

sample_rate=16000
model = Model(lang="en-us")
rec = KaldiRecognizer(model, sample_rate)
rec.SetWords(True)

process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                            sys.argv[1],
                            '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                            stdout=subprocess.PIPE)


WORDS_PER_LINE = 7

results = []
while True:
    data = process.stdout.read(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        results.append(rec.Result())
results.append(rec.FinalResult())

print (rec.SRTResult(results, WORDS_PER_LINE))
