#!/bin/bash
set -e -x

# Build libvosk (same as build-wheels.sh)
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
KALDI_ROOT=/opt/kaldi OPENFST_ROOT=/opt/kaldi/tools/openfst OPENBLAS_ROOT=/opt/kaldi/tools/OpenBLAS/install make -j $(nproc)

# Copy libs to output folder
mkdir -p /io/gemhouse/vosk-linux-x86_64
cp /opt/vosk-api/src/*.so /opt/vosk-api/src/vosk_api.h /io/gemhouse/vosk-linux-x86_64

# Copy libs to /io/src/ so the gem packaging stage (ruby:3.2 container) can
# find them via VOSK_SOURCE=/io -> src/lib*.so
cp /opt/vosk-api/src/*.so /io/src/
