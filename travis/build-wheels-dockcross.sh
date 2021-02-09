#!/bin/bash
set -e -x

# Build so file
cd /opt
git clone https://github.com/alphacep/vosk-api
cd /opt/vosk-api/src
KALDI_ROOT=/opt/kaldi make -j $(nproc)

# Decide architecture name
export VOSK_SOURCE=/opt/vosk-api
case $CROSS_TRIPLE in
    *armv7-*)
        export VOSK_ARCHITECTURE=armv7l
        ;;
    *aarch64-*)
        export VOSK_ARCHITECTURE=aarch64
        ;;
esac

# Copy library to output folder
mkdir -p /io/wheelhouse/linux-$VOSK_ARCHITECTURE
cp /opt/vosk-api/src/*.so /io/wheelhouse/linux-$VOSK_ARCHITECTURE

# Build wheel
pip3 wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
