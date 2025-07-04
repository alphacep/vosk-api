#!/usr/bin/env python3

import subprocess
import sys

from vosk_python import KaldiRecognizer, Model, set_log_level

SAMPLE_RATE = 16000

set_log_level(0)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, SAMPLE_RATE)

with subprocess.Popen(
	["ffmpeg", "-loglevel", "quiet", "-i", sys.argv[1], "-ar", str(SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"],
	stdout=subprocess.PIPE,
) as process:
	while True:
		data = process.stdout.read(4000)
		if len(data) == 0:
			break
		if rec.accept_waveform(data):
			pass
		else:
			pass
