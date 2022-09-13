#!/usr/bin/env python3

import wave
import sys
import json

from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(0)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit(1)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(rec.Result())
        sys.exit(1)

    else:
        jres = json.loads(rec.PartialResult())
        print(jres)

        if jres["partial"] == "one zero zero zero":
            print("We can reset recognizer here and start over")
            rec.Reset()
