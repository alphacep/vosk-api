#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SpkModel
import sys
import wave
import json
import os
import numpy as np

model_path = "model"
spk_model_path = "model-spk"

if not os.path.exists(model_path):
    print ("Please download the model from https://alphacephei.com/vosk/models and unpack as {} in the current folder.".format(model_path))
    exit (1)

if not os.path.exists(spk_model_path):
    print ("Please download the speaker model from https://alphacephei.com/vosk/models and unpack as {} in the current folder.".format(spk_model_path))
    exit (1)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

# Large vocabulary free form recognition
model = Model(model_path)
spk_model = SpkModel(spk_model_path)
#rec = KaldiRecognizer(model, wf.getframerate(), spk_model)
rec = KaldiRecognizer(model, wf.getframerate())
rec.SetSpkModel(spk_model)

def sorted_scores(fields):
    sorted_res = []
    for field in fields:
        sorted_res.append((field['speaker'], field['score']))
    sorted_res.sort(key = lambda x: x[1])
    sorted_res = sorted_res[::-1]
    return sorted_res


while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        if 'scores' in res:
            print("Sorted Scores of speakers:")
            print(sorted_scores(res['scores']))
        print ("Text:", res['text'])

print ("Note that second distance is not very reliable because utterance is too short. Utterances longer than 4 seconds give better xvector")

res = json.loads(rec.FinalResult())
if 'scores' in res:
    print("Sorted Scores of speakers:")
    print(sorted_scores(res['scores']))
