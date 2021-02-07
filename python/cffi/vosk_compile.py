#!/usr/bin/env python3

import os
from cffi import FFI
ffi = FFI()
ffi.set_source("_vosk", None)
ffi.cdef(os.popen("cpp ../../src/vosk_api.h").read())
ffi.compile()

