#!/usr/bin/env python3

import json

from vosk_python import KaldiRecognizer, Model

model = Model(lang="en-us")
rec = KaldiRecognizer(model, 8000)

res = json.loads(rec.final_result())
