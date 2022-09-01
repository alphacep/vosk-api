#!/usr/bin/env python3

import json

from vosk import Model, KaldiRecognizer

model = Model(lang="en-us")
rec = KaldiRecognizer(model, 8000)

res = json.loads(rec.FinalResult())
print(res)
