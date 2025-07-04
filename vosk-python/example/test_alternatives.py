import sys
import wave

from vosk_python import KaldiRecognizer, Model, set_log_level

set_log_level(0)

with wave.open(sys.argv[1], "rb") as wf:
	if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
		sys.exit(1)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, wf.getframerate())
rec.set_max_alternatives(10)
rec.set_words(True)

while True:
	data = wf.readframes(4000)
	if len(data) == 0:
		break
	if rec.accept_waveform(data):
		pass
	else:
		pass
