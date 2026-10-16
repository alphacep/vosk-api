#!/bin/bash
set -e -x

# Build so file (same as build-wheels-dockcross.sh)
cd /opt
git clone https://github.com/alphacep/vosk-api
cd /opt/vosk-api/src
KALDI_ROOT=/opt/kaldi EXTRA_LDFLAGS="-latomic" make -j $(nproc)

# Decide architecture name (same as Python)
case $CROSS_TRIPLE in
    *armv7-*)
        VOSK_MACHINE=armv7l
        VOSK_ARCHITECTURE=32bit
        ;;
    *i686-*)
        VOSK_MACHINE=x86
        VOSK_ARCHITECTURE=32bit
        ;;
    *aarch64-*)
        VOSK_MACHINE=aarch64
        VOSK_ARCHITECTURE=64bit
        ;;
    *riscv64-*)
        VOSK_MACHINE=riscv64
        VOSK_ARCHITECTURE=64bit
        ;;
esac

# Copy library to output folder
mkdir -p /io/gemhouse/vosk-linux-${VOSK_MACHINE}
cp /opt/vosk-api/src/*.so /opt/vosk-api/src/vosk_api.h /io/gemhouse/vosk-linux-${VOSK_MACHINE}

# Copy libs to /io/src/ so the gem packaging stage (ruby:3.2 container) can
# find them via VOSK_SOURCE=/io -> src/lib*.so
cp /opt/vosk-api/src/*.so /io/src/
