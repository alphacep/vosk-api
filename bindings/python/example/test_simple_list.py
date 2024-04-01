#!/usr/bin/env python3

import wave
import json
import sys
import time

from multiprocessing.dummy import Pool
from vosk import Model, KaldiRecognizer

#model = Model("vosk-model-ru-0.53-private-0.1")
model = Model("vosk-model-small-ru")

def recognize(line):
    fn = line.strip()
    wf = wave.open(fn, "rb")
    rec = KaldiRecognizer(model, wf.getframerate())

    results = []
    while True:
        data = wf.readframes(4000)
        if len(data) == 0:
            break

        rec.AcceptWaveform(data)
        while rec.GetNumPendingResults() > 0:
            time.sleep(0.05)

        while not rec.ResultsEmpty():
            jres = json.loads(rec.Result())
            if 'text' in jres:
                print (jres)
                results.append(jres['text'])
            rec.Pop()

    rec.Flush()

    while rec.GetNumPendingResults() > 0:
        time.sleep(0.05)

    while not rec.ResultsEmpty():
        jres = json.loads(rec.Result())
        if 'text' in jres:
            print (jres)
            results.append(jres['text'])
        rec.Pop()

    owf = open(fn.replace(".wav", ".hyp"), "w")
    owf.write("\n".join(results))

def main():
    p = Pool(30)
    p.map(recognize, open(sys.argv[1]).readlines())

main()
