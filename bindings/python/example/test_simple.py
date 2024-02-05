#!/usr/bin/env python3

import wave
import sys
import time

from vosk import Model, KaldiRecognizer, SetLogLevel

# You can set log level to -1 to disable debug messages
SetLogLevel(0)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit(1)

model = Model("vosk-model-ru-0.53-private-0.1")

rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(512)
    if len(data) == 0:
        break
    rec.AcceptWaveform(data)
    time.sleep(0.5)
    print (rec.Result())
