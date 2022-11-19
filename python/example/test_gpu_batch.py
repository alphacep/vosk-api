#!/usr/bin/env python3

import sys
import json

from vosk import BatchModel, BatchRecognizer, GpuInit
from timeit import default_timer as timer

TOT_SAMPLES = 0

GpuInit()

model = BatchModel("model")

with open(sys.argv[1]) as fn:
    fnames = fn.readlines()
    fds = [open(x.strip(), "rb") for x in fnames]
    uids = [fname.strip().split("/")[-1][:-4] for fname in fnames]
    recs = [BatchRecognizer(model, 16000) for x in fnames]
    results = [""] * len(fnames)

ended = set()

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
        TOT_SAMPLES += len(data)

    # Wait for results from CUDA
    model.Wait()

    # Retrieve and add results
    for i, fd in enumerate(fds):
        res = recs[i].Result()
        if len(res) != 0:
            results[i] = results[i] + " " + json.loads(res)["text"]

    if len(ended) == len(fds):
        break

end_time = timer()

for i, res in enumerate(results):
    print(uids[i], res.strip())

print("Processed %.3f seconds of audio in %.3f seconds (%.3f xRT)"
    % (TOT_SAMPLES / 16000.0 / 2,
    end_time - start_time,
    (TOT_SAMPLES / 16000.0 / 2 / (end_time - start_time))),
    file=sys.stderr)
