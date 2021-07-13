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
spk_sig = [8.945913, 0.502037, -4.809946, -3.049026, 6.339993, 0.789484, -5.59963, 9.547818, -0.681578, 0.80256, -1.510313, -4.393553, 1.290226, -2.251539, -5.015003, -1.197941, 0.285751, -2.440238, -3.641057, -2.557999, 3.224791, -2.303548, 1.2756, 3.534009, -2.91004, 6.074108, 5.82937, 0.173965, -3.096735, 1.829986, 1.274339, -1.362121, 1.5895, -4.841635, -0.939619, 1.707323, -3.516852, -1.191185, -4.915336, 0.412464, 0.71046, -3.999348, 4.24368, 1.446671, 4.901538, 4.882139, -1.297878, -4.468873, 1.138283, 1.198755, 1.993544, 0.259015, 3.187727, -0.188859, 5.49298, 4.014388, 3.119898, -1.873115, -1.063644, -4.28518, 10.454569, -2.927687, 1.816494, -2.543615, -2.787302, -4.03351, -2.662941, -3.584681, 1.466118, -3.7294, 7.0945, 1.075484, 1.478081, 1.283387, -2.014766, -0.693308, 0.8249, -2.3099, 0.274937, 1.368053, 3.161945, 3.701893, -4.25515, 6.011588, -3.549611, 0.503999, -0.578537, -1.749809, 4.441003, -3.038565, 2.648571, -4.085972, -3.386127, -1.363227, -4.740501, 0.812496, 3.764253, -2.538162, -2.824445, -5.776532, -1.381555, 1.689328, 0.669544, 1.315659, 3.145844, 2.729119, -3.20377, 3.607407, -0.152904, -2.676708, 1.113107, 2.872794, -0.651113, -1.62337, 3.344232, -0.515282, -1.215563, -4.636061, 1.761013, -2.917052, -4.98283, 0.693441, 1.206074, -0.103077, 3.158075, -4.308764, 1.078705, 2.433186, 0.473338, 6.541557, -2.490289, -0.305082, 0.716277, -1.705658, 0.653532, 1.763302, -2.051252, -2.756943, 4.55014, -0.126923, -5.420956, 1.290554, 1.044374, 2.860218, -5.542233, 1.95986, -2.058065, -1.153816, 1.695832, 2.159567]
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
