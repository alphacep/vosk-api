#!/bin/bash
set -e -x

# Build libvosk (same as build-wheels-winaarch64.sh)
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
EXTRA_LDFLAGS=-Wl,--out-implib,libvosk.lib CXX=aarch64-w64-mingw32-g++ EXT=dll KALDI_ROOT=/opt/kaldi/kaldi OPENFST_ROOT=/opt/kaldi/local OPENBLAS_ROOT=/opt/kaldi/local make -j $(nproc)

# Copy dlls to output folder
mkdir -p /io/gemhouse/vosk-winaarch64
cp /opt/vosk-api/src/*.{dll,lib} /opt/vosk-api/src/vosk_api.h /io/gemhouse/vosk-winaarch64

# Copy dlls to /io/src/ for gem packaging stage
cp /opt/vosk-api/src/*.dll /io/src/
