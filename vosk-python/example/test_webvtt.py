#!/usr/bin/env python3

import json
import subprocess
import sys
import textwrap

from vosk_python import KaldiRecognizer, Model, set_log_level
from webvtt import Caption, WebVTT

SAMPLE_RATE = 16000
WORDS_PER_LINE = 7

set_log_level(-1)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.set_words(True)


def timestring(seconds: float) -> str:
	minutes = seconds / 60
	seconds = seconds % 60
	hours = int(minutes / 60)
	minutes = int(minutes % 60)
	return f"{hours:d}:{minutes:02d}:{seconds:06.3f}"


def transcribe():
	command = [
		"ffmpeg",
		"-nostdin",
		"-loglevel",
		"quiet",
		"-i",
		sys.argv[1],
		"-ar",
		str(SAMPLE_RATE),
		"-ac",
		"1",
		"-f",
		"s16le",
		"-",
	]
	with subprocess.Popen(command, stdout=subprocess.PIPE) as process:
		results = []
		while True:
			data = process.stdout.read(4000)
			if len(data) == 0:
				break
			if rec.accept_waveform(data):
				results.append(rec.result())
		results.append(rec.final_result())

		vtt = WebVTT()
		for _, res in enumerate(results):
			words = json.loads(res).get("result")
			if not words:
				continue

			start = timestring(words[0]["start"])
			end = timestring(words[-1]["end"])
			content = " ".join([w["word"] for w in words])

			caption = Caption(start, end, textwrap.fill(content))
			vtt.captions.append(caption)

		# save or return webvtt
		if len(sys.argv) > 2:
			vtt.save(sys.argv[2])
		else:
			pass


if __name__ == "__main__":
	if not 1 < len(sys.argv) < 4:
		sys.exit(1)
	transcribe()
