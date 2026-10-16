#!/bin/bash
set -e -x

# Build libvosk (same as build-wheels-win32.sh)
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
EXTRA_LDFLAGS=-Wl,--out-implib,libvosk.lib CXX=i686-w64-mingw32-g++-posix EXT=dll KALDI_ROOT=/opt/kaldi/kaldi OPENFST_ROOT=/opt/kaldi/local OPENBLAS_ROOT=/opt/kaldi/local make -j $(nproc)

# Collect runtime dependencies
cp /usr/lib/gcc/i686-w64-mingw32/*-posix/libstdc++-6.dll /opt/vosk-api/src
cp /usr/lib/gcc/i686-w64-mingw32/*-posix/libgcc_s_sjlj-1.dll /opt/vosk-api/src
cp /usr/i686-w64-mingw32/lib/libwinpthread-1.dll /opt/vosk-api/src

# Copy dlls to output folder
mkdir -p /io/gemhouse/vosk-win32
cp /opt/vosk-api/src/*.{dll,lib} /opt/vosk-api/src/vosk_api.h /io/gemhouse/vosk-win32

# Copy dlls to /io/src/ for gem packaging stage
cp /opt/vosk-api/src/*.dll /io/src/
