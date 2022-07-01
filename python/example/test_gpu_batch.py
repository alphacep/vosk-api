#!/usr/bin/env python3

import sys
import os
import wave
from time import sleep
import json
from timeit import default_timer as timer


from vosk import BatchModel, BatchRecognizer, GpuInit

GpuInit()

model = BatchModel()

fnames = open(sys.argv[1]).readlines()
fds = [open(x.strip(), "rb") for x in fnames]
uids = [fname.strip().split('/')[-1][:-4] for fname in fnames]
recs = [BatchRecognizer(model, 16000) for x in fnames]
results = [""] * len(fnames)
ended = set()
tot_samples = 0

start_time = timer()

while True:

    # Feed in the data
    for i, fd in enumerate(fds):
        if i in ended:
            continue
        data = fd.read(8000)
        if len(data) == 0:
            recs[i].FinishStream()
            ended.add(i)
            continue
        recs[i].AcceptWaveform(data)
        tot_samples += len(data)

    # Wait for results from CUDA
    model.Wait()

    # Retrieve and add results
    for i, fd in enumerate(fds):
       res = recs[i].Result()
       if len(res) != 0:
           results[i] = results[i] + " " + json.loads(res)['text']

    if len(ended) == len(fds):
        break

end_time = timer()

for i in range(len(results)):
    print (uids[i], results[i].strip())

print ("Processed %.3f seconds of audio in %.3f seconds (%.3f xRT)" % (tot_samples / 16000.0 / 2, end_time - start_time, 
    (tot_samples / 16000.0 / 2 / (end_time - start_time))), file=sys.stderr)
