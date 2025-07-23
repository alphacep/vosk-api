#!/usr/bin/env python3

import wave
import json
import sys
import os
import time
from timeit import default_timer as timer

from multiprocessing.dummy import Pool
from vosk import Model, KaldiRecognizer

model = Model("vosk-model-ru-0.54-private-0.1")
#model = Model("vosk-model-small-ru")

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
    start = timer()
    p = Pool(20)
    p.map(recognize, open(sys.argv[1]).readlines())
    allsize = sum([os.path.getsize(f.strip()) for f in open(sys.argv[1]).readlines()]) / 8000.0 / 2
    dur = timer() - start
    print (f"Recognized {allsize:.2f} seconds in {dur} seconds speed {dur / allsize:.3f} x RT")

main()
