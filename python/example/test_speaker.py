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


# We compare speakers with cosine distance. We can keep one or several fingerprints for the speaker in a database
# to distingusih among users.
spk_sig = [-3.599562, -2.026062, 2.619174, 2.734565, -1.662937, -4.74859, -1.302216, 1.96882, -2.438875, -0.862439, -1.382468, -3.85917, -1.282347, -0.431352, -2.920996, -1.98946, 1.413224, -1.546382, 2.857671, 0.807126, -0.332029, -3.201846, 1.011603, 0.958886, 0.489368, -0.452923, 1.651212, 0.795769, 0.984747, -0.986164, 0.166111, -0.101681, -2.088426, -1.355594, 0.05438, 0.976541, 0.196736, 0.353433, -3.655376, 2.283057, -1.70085, -1.589682, -4.005692, -0.220475, -1.843239, -2.215318, 3.458803, -1.619743, 0.222303, 1.464833, 0.407315, 1.67935, 0.730794, 0.736013, 1.083858, 0.397476, -0.918136, 2.689642, 3.068224, -1.220341, 0.651497, 2.137368, -1.19811, -1.18176, -2.236404, -3.717717, 3.016081, -0.177697, 1.481231, 0.374173, 1.200841, -0.23104, -2.221116, 1.406717, 0.248455, 0.912048, -0.854026, -2.049804, 0.521391, -2.027633, -1.402856, -1.51159, -0.164994, 0.968201, -0.013585, 1.747202, 1.801239, -1.939345, -1.370392, 0.994743, 1.965558, 2.243757, -0.122754, -2.214027, -2.606432, 1.938032, 1.276491, 0.216464, -0.115291, -2.254721, 1.976314, -1.080948, 0.140106, -1.462986, 0.553232, -0.357925, -1.769019, 0.390051, -1.026521, 0.115607, -0.860444, -0.929102, 2.422206, 0.738637, -1.102857, 1.962766, -1.027656, -1.240682, -1.571711, 1.3434, -2.104941, 0.652695, 0.674792, 0.022579, -1.697821, -0.975781, -0.259832, -1.839605, 1.63971, -1.812947, 1.289088, 1.229352, -1.334593, -1.65641, -0.690415, 0.129282, 0.5189, 0.187057, 0.435663, -0.658561, -0.119598, -0.694887, -0.55879, 0.640803, -0.878957, -0.949996, -0.564727, 0.989271, -0.628733, 0.958241]
def cosine_dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)


# We can calculate PLDA scores using vosk-api which has better quility
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
        if 'spk' in res:
            print ("X-vector:", res['spk'])
            print ("Speaker distance:", cosine_dist(spk_sig, res['spk']), "based on", res['spk_frames'], "frames")
        if 'scores' in res:
            print("Sorted Scores of speakers:")
            print(sorted_scores(res['scores']))
        print ("Text:", res['text'])

print ("Note that second distance is not very reliable because utterance is too short. Utterances longer than 4 seconds give better xvector")

res = json.loads(rec.FinalResult())
if 'scores' in res:
    print("Sorted Scores of speakers:")
    print(sorted_scores(res['scores']))
if 'spk' in res:
   print ("X-vector:", res['spk'])
   print ("Speaker distance:", cosine_dist(spk_sig, res['spk']), "based on", res['spk_frames'], "frames")
