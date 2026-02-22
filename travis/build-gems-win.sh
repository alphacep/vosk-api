#!/bin/bash
set -e -x

# Build libvosk (same as build-wheels-win.sh)
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
EXTRA_LDFLAGS=-Wl,--out-implib,libvosk.lib CXX=x86_64-w64-mingw32-g++-posix EXT=dll KALDI_ROOT=/opt/kaldi/kaldi OPENFST_ROOT=/opt/kaldi/local OPENBLAS_ROOT=/opt/kaldi/local make -j $(nproc)

# Collect runtime dependencies (same as build-wheels-win.sh)
cp /usr/lib/gcc/x86_64-w64-mingw32/*-posix/libstdc++-6.dll /opt/vosk-api/src
cp /usr/lib/gcc/x86_64-w64-mingw32/*-posix/libgcc_s_seh-1.dll /opt/vosk-api/src
cp /usr/x86_64-w64-mingw32/lib/libwinpthread-1.dll /opt/vosk-api/src

# Copy dlls to output folder
mkdir -p /io/gemhouse/vosk-win64
cp /opt/vosk-api/src/*.{dll,lib} /opt/vosk-api/src/vosk_api.h /io/gemhouse/vosk-win64

# Copy dlls to /io/src/ so the gem packaging stage (ruby:3.2 container) can
# find them via VOSK_SOURCE=/io -> src/*.dll
cp /opt/vosk-api/src/*.dll /io/src/
