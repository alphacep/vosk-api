import os
from pathlib import Path

from cffi import FFI

vosk_root = Path(os.environ.get("VOSK_SOURCE", ".."))
cpp_command = f"cpp {vosk_root / 'src/vosk_api.h'}"

ffibuilder = FFI()
ffibuilder.set_source("vosk_python.vosk_cffi", None)
ffibuilder.cdef(Path(cpp_command).read_text())

if __name__ == "__main__":
	ffibuilder.compile(verbose=True)
