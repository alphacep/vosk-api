#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import sys
import json

model = Model(lang="en-us")
rec = KaldiRecognizer(model, 8000)

res = json.loads(rec.FinalResult())
print (res)
