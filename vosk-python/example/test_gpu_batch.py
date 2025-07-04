#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from timeit import default_timer as timer

from vosk_python import BatchModel, BatchRecognizer, gpu_init

TOT_SAMPLES = 0

gpu_init()

model = BatchModel("model")

with Path.open(Path(sys.argv[1])) as fn:
	fnames = fn.readlines()
	fds = [open(x.strip(), "rb") for x in fnames]  # noqa: SIM115, PTH123
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
			recs[i].finish_stream()
			ended.add(i)
			continue
		recs[i].accept_waveform(data)
		TOT_SAMPLES += len(data)

	# Wait for results from CUDA
	model.wait()

	# Retrieve and add results
	for i, _ in enumerate(fds):
		res = recs[i].result()
		if len(res) != 0:
			results[i] = results[i] + " " + json.loads(res)["text"]

	if len(ended) == len(fds):
		break

end_time = timer()
