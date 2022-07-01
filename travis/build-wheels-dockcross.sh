#!/bin/bash
set -e -x

# Build so file
cd /opt
git clone https://github.com/alphacep/vosk-api
cd /opt/vosk-api/src
KALDI_ROOT=/opt/kaldi EXTRA_LDFLAGS="-latomic" make -j $(nproc)

# Decide architecture name
export VOSK_SOURCE=/opt/vosk-api
case $CROSS_TRIPLE in
    *armv7-*)
        export VOSK_ARCHITECTURE=armv7l
        ;;
    *aarch64-*)
        export VOSK_ARCHITECTURE=aarch64
        ;;
    *i686-*)
        export VOSK_ARCHITECTURE=x86
        ;;
    *riscv64-*)
        export VOSK_ARCHITECTURE=riscv64
        ;;
esac

# Copy library to output folder
mkdir -p /io/wheelhouse/vosk-linux-$VOSK_ARCHITECTURE
cp /opt/vosk-api/src/*.so /opt/vosk-api/src/vosk_api.h /io/wheelhouse/vosk-linux-$VOSK_ARCHITECTURE

# Build wheel
python3 -m pip install requests tqdm srt
python3 -m pip wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
