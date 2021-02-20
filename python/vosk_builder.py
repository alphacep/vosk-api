#!/usr/bin/env python3

import os
from cffi import FFI

vosk_root=os.environ.get("VOSK_SOURCE", "..")
cpp_command = "cpp " + vosk_root + "/src/vosk_api.h"

ffibuilder = FFI()
ffibuilder.set_source("vosk.vosk_cffi", None)
ffibuilder.cdef(os.popen(cpp_command).read())

if __name__ == '__main__':
    ffibuilder.compile(verbose=True)
