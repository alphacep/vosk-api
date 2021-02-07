#!/usr/bin/env python3

import os
from cffi import FFI

ffibuilder = FFI()
ffibuilder.set_source("vosk.vosk_cffi", None)
ffibuilder.cdef(os.popen("cpp ../src/vosk_api.h").read())

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
