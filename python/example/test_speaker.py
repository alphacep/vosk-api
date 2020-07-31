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
    print ("Please download the model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as {} in the current folder.".format(model_path))
    exit (1)

if not os.path.exists(spk_model_path):
    print ("Please download the speaker model from https://github.com/alphacep/vosk-api/blob/master/doc/models.md and unpack as {} in the current folder.".format(spk_model_path))
    exit (1)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print ("Audio file must be WAV format mono PCM.")
    exit (1)

# Large vocabulary free form recognition
model = Model(model_path)
spk_model = SpkModel(spk_model_path)
rec = KaldiRecognizer(model, spk_model, wf.getframerate())

# We compare speakers with cosine distance. We can keep one or several fingerprints for the speaker in a database
# to distingusih among users.
spk_sig = [4.658117, 1.277387, 3.346158, -1.473036, -2.15727, 2.461757, 3.76756, -1.241252, 2.333765, 0.642588, -2.848165, 1.229534, 3.907015, 1.726496, -1.188692, 1.16322, -0.668811, -0.623309, 4.628018, 0.407197, 0.089955, 0.920438, 1.47237, -0.311365, -0.437051, -0.531738, -1.591781, 3.095415, 0.439524, -0.274787, 4.03165, 2.665864, 4.815553, 1.581063, 1.078242, 5.017717, -0.089395, -3.123428, 5.34038, 0.456982, 2.465727, 2.131833, 4.056272, 1.178392, -2.075712, -1.568503, 0.847139, 0.409214, 1.84727, 0.986758, 4.222116, 2.235512, 1.369377, 4.283126, 2.278125, -1.467577, -0.999971, 3.070041, 1.462214, 0.423204, 2.143578, 0.567174, -2.294655, 1.864723, 4.307356, 2.610872, -1.238721, 0.551861, 2.861954, 0.59613, -0.715396, -1.395357, 2.706177, -2.004444, 2.055255, 0.458283, 1.231968, 3.48234, 2.993858, 0.402819, 0.940885, 0.360162, -2.173674, -2.504609, 0.329541, 3.653913, 3.638025, -1.406409, 2.14059, 1.662765, -0.991323, 0.770921, 0.010094, 3.775469, 1.847511, 2.074432, -1.928593, 0.807414, 2.964505, 0.128597, 1.297962, 2.645227, 0.136405, -2.543087, 0.932246, 2.405783, -2.122267, 3.044013, 0.486728, 4.395338, 0.474267, 0.781297, 1.694144, -0.831078, -0.462362, -0.964715, 3.187863, 6.008708, 1.725954, 3.667886, -1.467623, 3.370667, 2.72555, -0.796541, 2.416543, 0.675401, -0.737634, -1.709676]

def cosine_dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        print ("Text:", res['text'])
        print ("X-vector:", res['spk'])
        print ("Speaker distance:", cosine_dist(spk_sig, res['spk']))

res = json.loads(rec.FinalResult())
print ("Text:", res['text'])
print ("X-vector:", res['spk'])
print ("Speaker distance:", cosine_dist(spk_sig, res['spk']))
