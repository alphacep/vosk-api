#!/usr/bin/env python3

import json
import sys
import wave
from multiprocessing.dummy import Pool
from pathlib import Path
from typing import Any

from vosk_python import KaldiRecognizer, Model

model = Model("en-us")


def recognize(line: str) -> str:
	uid, fn = line.split()
	with wave.open(fn, "rb") as wf:
		rec = KaldiRecognizer(model, wf.getframerate())

		text = ""
		while True:
			data = wf.readframes(1000)
			if len(data) == 0:
				break
			if rec.accept_waveform(data):
				jres: dict[str, Any] = json.loads(rec.result())
				text = text + " " + jres["text"]
		jres = json.loads(rec.final_result())
		text = text + " " + jres["text"]
		return uid + text


def main() -> None:
	p = Pool(8)
	with Path(sys.argv[1]).open(encoding="utf-8") as f:
		lines = f.readlines()
		p.map(recognize, lines)


if __name__ == "__main__":
	main()
