#!/usr/bin/python3

from vosk import Model, KaldiRecognizer, SpkModel
import sys
import json
import os
import numpy as np

model_path = "model-en"
spk_model_path = "model-spk"

if not os.path.exists(model_path):
    print ("Please download the model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as {} in the current folder.".format(model_path))
    exit (1)

if not os.path.exists(spk_model_path):
    print ("Please download the speaker model from https://github.com/alphacep/kaldi-android-demo/releases and unpack as {} in the current folder.".format(spk_model_path))
    exit (1)

model = Model(model_path)

spk_model = SpkModel(spk_model_path)

# Large vocabulary free form recognition
rec = KaldiRecognizer(model, spk_model, 16000)

wf = open(sys.argv[1], "rb")
wf.read(44) # skip header

spk_sig = [5.64308, 4.23898, 1.119433, -0.810904, 2.115443, 2.328436, 6.135152, 1.348195, 2.60771, 1.020717, 4.324225, -0.873012, 6.123375, 4.903791, 0.064803, 4.66212, 3.502724, 2.535861, 5.452417, 7.081769, -0.823969, -5.167974, 8.568919, 4.159035, 5.314441, 3.688272, 5.730379, 4.463213, 7.227232, 3.538961, 3.316218, 1.269628, -1.902378, 3.512679, -1.947611, -1.520158, 3.80928, -2.721601, 5.359588, 2.942463, -7.474174, 3.788054, 0.303426, 4.951366, 1.72281, -1.867125, -3.574615, 3.622509, 4.803109, 2.829714, 1.528521, 6.408293, 0.820131, 5.066522, 2.836125, 2.867029, 3.725267, 0.505927, 1.462984, 5.001863, -3.838309, -2.45902, 3.992581, 4.451616, 2.865211, -1.148313, 4.996399, -3.473454, 2.876967, 3.940124, 7.553079, 0.373356, 1.396561, 2.686691, 2.094895, 0.913796, -0.286909, 3.540179, 4.904687, 0.84554, 7.585956, 1.017081, 0.168355, 6.672327, 4.092033, -4.240158, -2.017081, -0.813043, 6.468298, 4.115041, 2.231936, 2.370055, 4.972295, 5.58382, 6.022872, 2.706988, 5.248096, -1.918003, 8.259204, -0.900911, 1.961962, 2.349709, 3.290093, 3.344172, 3.307027, 4.203372, -0.315103, 5.61919, -3.229496, 3.777309, 4.328595, 1.461014, 2.622894, 0.315525, 5.447259, 5.407609, 5.339016, 1.604555, 5.359932, 0.090242, 0.535306, 4.724705, 4.692502, 0.5783, -5.436688, -4.915511, 1.959807, 2.825248]

def dist(x, y):
    nx = np.array(x)
    ny = np.array(y)
    return 1 - np.dot(nx, ny) / np.linalg.norm(nx) / np.linalg.norm(ny)

while True:
    data = wf.read(2000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        res = json.loads(rec.Result())
        print (res)
        print ("Spk distance", dist(spk_sig, res['spk']))
    else:
        res = json.loads(rec.PartialResult())
        print (res)

res = json.loads(rec.FinalResult())
print (res)
print ("Spk distance", dist(spk_sig, res['spk']))

