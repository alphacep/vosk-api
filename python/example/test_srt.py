#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer, SetLogLevel
import sys
import subprocess

SetLogLevel(-1)

sample_rate=16000
model = Model(lang="en-us")
rec = KaldiRecognizer(model, sample_rate)
rec.SetWords(True)

stream = subprocess.Popen(['ffmpeg', '-loglevel', 'quiet', '-i',
                            sys.argv[1],
                            '-ar', str(sample_rate) , '-ac', '1', '-f', 's16le', '-'],
                            stdout=subprocess.PIPE).stdout

print(rec.SrtResult(stream))
