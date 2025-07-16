#!/usr/bin/env python3

import wave
import sys
import time

from vosk import Model, KaldiRecognizer, SetLogLevel

# You can set log level to -1 to disable debug messages
SetLogLevel(0)

wf = wave.open(sys.argv[1], "rb")
if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getcomptype() != "NONE":
    print("Audio file must be WAV format mono PCM.")
    sys.exit(1)

model = Model("vosk-model-ru-0.54-private-0.1")
#model = Model("vosk-model-small-ru")

rec = KaldiRecognizer(model, wf.getframerate())

while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break

    # Feed into waveform
    rec.AcceptWaveform(data)

    # Wait for processing
    while rec.GetNumPendingResults() > 0:
        time.sleep(0.05)

    # Retrieve the results
    while not rec.ResultsEmpty():
        print (rec.Result())
        rec.Pop()

rec.Flush()

# Wait for processing
while rec.GetNumPendingResults() > 0:
    time.sleep(0.05)

# Retrieve the results
while not rec.ResultsEmpty():
    print (rec.Result())
    rec.Pop()
