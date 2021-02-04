#!/usr/bin/env python3

from cffi import FFI
import os
ffi = FFI()
ffi.set_source("_vosk", None)
ffi.cdef(os.popen("cpp ../../src/vosk_api.h").read())
ffi.compile()

C = ffi.dlopen("libvosk.so")

model = C.vosk_model_new("model".encode('utf-8'))
rec = C.vosk_recognizer_new(model, 16000)

with open("test.wav", "rb") as wf:

    while True:
        data = wf.read(8000)
        if len(data) == 0:
            break
        if C.vosk_recognizer_accept_waveform(rec, data, len(data)):
            print(ffi.string(C.vosk_recognizer_result(rec)).decode('utf-8'))
        else:
            print(ffi.string(C.vosk_recognizer_partial_result(rec)).decode('utf-8'))
    print(ffi.string(C.vosk_recognizer_final_result(rec)).decode('utf-8'))

C.vosk_recognizer_free(rec)
C.vosk_model_free(model)
