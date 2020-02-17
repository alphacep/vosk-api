#!/usr/bin/python3

from vosk import Model, KaldiRecognizer
import sys
import json
import os

if not os.path.exists("model-en"):
    print ("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as 'model' in the current folder.")
    exit (1)


model = Model("model-en")

# You can also specify the possible word list
rec = KaldiRecognizer(model, 16000, "zero oh one two three four five six seven eight nine")

wf = open(sys.argv[1], "rb")
wf.read(44) # skip header

while True:
    data = wf.read(2000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        print (res)
    else:
        res = json.loads(rec.PartialResult())
        print (res)

res = json.loads(rec.FinalResult())
print (res)
