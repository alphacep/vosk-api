#!/usr/bin/python3

from vosk import Model, KaldiRecognizer
import sys
import json
import os
import wave

if not os.path.exists("model"):
    print ("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as 'model' in the current folder.")
    exit (1)


wf_name = sys.argv[1]
wf = wave.open(wf_name, "rb")

# check that the WAV is 16-bit mono
assert 1 == wf.getnchannels()
assert 2 == wf.getsampwidth()
assert 'NONE' == wf.getcomptype()

model = Model("model")
if model.GetSampleFrequency() < wf.getframerate():
    print('Model sample frequency is lower than WAV file. Enabling downsampling.')
    model.SetAllowDownsample(True)
elif model.GetSampleFrequency() > wf.getframerate():
    print('Model sample frequency is higher than WAV file. Enabling upsampling. You may experience inaccurate results.')
    model.SetAllowUpsample(True)

# Large vocabulary free form recognition
rec = KaldiRecognizer(model, wf.getframerate())

# You can also specify the possible word list
# rec = KaldiRecognizer(model, wf.getframerate(), "zero oh one two three four five six seven eight nine")

while True:
    data = wf.readframes(1000)
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
