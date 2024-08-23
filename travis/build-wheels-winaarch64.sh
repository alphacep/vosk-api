#!/bin/bash
set -e -x

# Build libvosk
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
EXTRA_LDFLAGS=-Wl,--out-implib,libvosk.lib CXX=aarch64-w64-mingw32-g++ EXT=dll KALDI_ROOT=/opt/kaldi/kaldi OPENFST_ROOT=/opt/kaldi/local OPENBLAS_ROOT=/opt/kaldi/local make -j $(nproc)

# Copy dlls to output folder
mkdir -p /io/wheelhouse/vosk-winaarch64
cp /opt/vosk-api/src/*.{dll,lib} /opt/vosk-api/src/vosk_api.h /io/wheelhouse/vosk-winaarch64

# Build wheel and put to the output folder
export VOSK_SOURCE=/opt/vosk-api
export VOSK_SYSTEM=Windows
export VOSK_ARCHITECTURE=64bit
python3 -m pip -v wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
