#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import os
import wave
import subprocess
import srt
import json
import datetime

SetLogLevel(-1)

if not os.path.exists("model"):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    exit (1)

sample_rate=16000
model = Model("model")
rec = KaldiRecognizer(model, sample_rate)

process = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                            sys.argv[1],
                            '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                            stdout=subprocess.PIPE)


def transcribe():
    results = []
    subs = []
    while True:
       data = process.stdout.read(4000)
       if len(data) == 0:
           break
       if rec.AcceptWaveform(data):
           results.append(rec.Result())
    results.append(rec.FinalResult())

    for i, res in enumerate(results):
       jres = json.loads(res)
       s = srt.Subtitle(index=i, 
                   content=jres['text'], 
                   start=datetime.timedelta(seconds=jres['result'][0]['start']), 
                   end=datetime.timedelta(seconds=jres['result'][-1]['end']))
       subs.append(s)
    return subs

print (srt.compose(transcribe()))

