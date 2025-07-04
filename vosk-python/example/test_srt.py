#!/usr/bin/env python3

import subprocess
import sys

from vosk_python import KaldiRecognizer, Model, set_log_level

SAMPLE_RATE = 16000

set_log_level(-1)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.set_words(True)

with subprocess.Popen(
	["ffmpeg", "-loglevel", "quiet", "-i", sys.argv[1], "-ar", str(SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"],
	stdout=subprocess.PIPE,
).stdout as stream:
	pass
