#!/usr/bin/env python3

# prerequisites: as described in https://alphacephei.com/vosk/install and also python module `sounddevice` (simply run command `pip install sounddevice`)
# Example usage using Dutch (nl) recognition model: `python test_microphone.py -m nl`
# For more help run: `python test_microphone.py -h`

import argparse
import queue
from pathlib import Path
from typing import Any

import sounddevice as sd
from vosk_python import KaldiRecognizer, Model

q = queue.Queue()


def int_or_str(text: str):
	"""Helper function for argument parsing."""
	try:
		return int(text)
	except ValueError:
		return text


def callback(indata: Any, frames: Any, time: Any, status: bool):
	"""Called (from a separate thread) for each audio block."""
	if status:
		pass
	q.put(bytes(indata))


parser = argparse.ArgumentParser(add_help=False)
parser.add_argument("-l", "--list-devices", action="store_true", help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
	parser.exit(0)
parser = argparse.ArgumentParser(
	description=__doc__,
	formatter_class=argparse.RawDescriptionHelpFormatter,
	parents=[parser],
)
parser.add_argument("-f", "--filename", type=str, metavar="FILENAME", help="audio file to store recording to")
parser.add_argument("-d", "--device", type=int_or_str, help="input device (numeric ID or substring)")
parser.add_argument("-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument("-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
args = parser.parse_args(remaining)

try:
	if args.samplerate is None:
		device_info = sd.query_devices(args.device, "input")
		# soundfile expects an int, sounddevice provides a float:
		args.samplerate = int(device_info["default_samplerate"])

	model = Model(lang="en-us") if args.model is None else Model(lang=args.model)

	dump_fn = Path.open(Path(args.filename), "wb") if args.filename else None

	with sd.RawInputStream(
		samplerate=args.samplerate,
		blocksize=8000,
		device=args.device,
		dtype="int16",
		channels=1,
		callback=callback,
	):
		rec = KaldiRecognizer(model, args.samplerate)
		while True:
			data = q.get()
			if rec.accept_waveform(data):
				pass
			else:
				pass
			if dump_fn is not None:
				dump_fn.write(data)

except KeyboardInterrupt:
	parser.exit(0)
except Exception as e:
	parser.exit(type(e).__name__ + ": " + str(e))
