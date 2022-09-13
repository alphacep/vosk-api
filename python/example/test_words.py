#!/usr/bin/env python3

import wave
import sys

from vosk import Model, KaldiRecognizer

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit(1)

model = Model(lang="en-us")

# You can also specify the possible word or phrase list as JSON list,
# the order doesn't have to be strict
rec = KaldiRecognizer(model,
    wf.getframerate(),
    '["oh one two three", "four five six", "seven eight nine zero", "[unk]"]')

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        print(rec.Result())
        rec.SetGrammar('["one zero one two three oh", "four five six", "seven eight nine zero", "[unk]"]')
    else:
        print(rec.PartialResult())

print(rec.FinalResult())
