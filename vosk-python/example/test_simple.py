#!/usr/bin/env python3

import sys
import wave

from vosk_python import KaldiRecognizer, Model, set_log_level

# You can set log level to -1 to disable debug messages
set_log_level(0)

with wave.open(sys.argv[1], "rb") as wf:
	if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
		sys.exit(1)

model = Model(lang="en-us")

# You can also init model by name or with a folder path
# model = Model(model_name="vosk-model-en-us-0.21")
# model = Model("models/en")

rec = KaldiRecognizer(model, wf.getframerate())
rec.set_words(True)
rec.set_partial_words(True)

while True:
	data = wf.readframes(4000)
	if len(data) == 0:
		break
	if rec.accept_waveform(data):
		pass
	else:
		pass
