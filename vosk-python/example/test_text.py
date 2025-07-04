#!/usr/bin/env python3

import json
import sys
from pathlib import Path

from vosk_python import KaldiRecognizer, Model

model = Model(lang="en-us")

# Large vocabulary free form recognition
rec = KaldiRecognizer(model, 16000)

# You can also specify the possible word list
# rec = KaldiRecognizer(model, 16000, "zero oh one two three four five six seven eight nine")

with Path.open(Path(sys.argv[1]), "rb") as wf:
	wf.read(44)  # skip header

	while True:
		data = wf.read(4000)
		if len(data) == 0:
			break
		if rec.accept_waveform(data):
			res = json.loads(rec.result())

	res = json.loads(rec.final_result())
