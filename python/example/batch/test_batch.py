#!/usr/bin/env python3

import sys
import os
import wave
from time import sleep

from vosk import Model, BatchRecognizer, GpuInit

GpuInit()

rec = BatchRecognizer()

fnames = open("tedlium.list").readlines()
fds = [open(x.strip(), "rb") for x in fnames]
ended = set()
while True:

    for i, fd in enumerate(fds):
        if i in ended:
            continue
        data = fd.read(8000)
        if len(data) == 0:
            rec.FinishStream(i)
            ended.add(i)
            continue
        rec.AcceptWaveform(i, data)

    sleep(0.3)
    for i, fd in enumerate(fds):
       res = rec.Result(i)
       print (i, res)

    if len(ended) == len(fds):
        break

sleep(20)
print ("Done")
for i, fd in enumerate(fds):
   res = rec.Result(i)
   print (i, res)
rec.Wait()
