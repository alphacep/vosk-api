#!/usr/bin/env python3

import sys
import os
import wave
from time import sleep
import json
from timeit import default_timer as timer


from vosk import Model, BatchRecognizer, GpuInit

GpuInit()

rec = BatchRecognizer()

# Read list of files from the file
fnames = open(sys.argv[1]).readlines()
fds = [open(x.strip(), "rb") for x in fnames]
uids = [fname.strip().split('/')[-1][:-4] for fname in fnames]
results = [""] * len(fnames)
ended = set()
tot_samples = 0

start_time = timer()

while True:

    # Feed in the data
    for i, fd in enumerate(fds):
        if i in ended:
            continue
        data = fd.read(16000)
        if len(data) == 0:
            rec.FinishStream(i)
            ended.add(i)
            continue
        rec.AcceptWaveform(i, data)
        tot_samples += len(data)

    # Wait for results from CUDA
    rec.Wait()

    # Retrieve and add results
    for i, fd in enumerate(fds):
       res = rec.Result(i)
       if len(res) != 0:
           results[i] = results[i] + " " + json.loads(res)['text']

    if len(ended) == len(fds):
        break

end_time = timer()

for i in range(len(results)):
    print (uids[i], results[i].strip())

print ("Processed %d seconds of audio in %d seconds (%f xRT)" % (tot_samples / 16000.0 / 2, end_time - start_time, 
    (tot_samples / 16000.0 / 2 / (end_time - start_time))), file=sys.stderr)
