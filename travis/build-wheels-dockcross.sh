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
        export VOSK_MACHINE=armv7l
        export VOSK_ARCHITECTURE=32bit
        ;;
    *armv7l-linux-musleabihf*)
        export VOSK_MACHINE=armv7l
        export VOSK_ARCHITECTURE=32bit
        export VOSK_VARIANT="-musl"
        ;;
    *i686-*)
        export VOSK_MACHINE=x86
        export VOSK_ARCHITECTURE=32bit
        ;;
    *aarch64-*)
        export VOSK_MACHINE=aarch64
        export VOSK_ARCHITECTURE=64bit
        ;;
    *riscv64-*)
        export VOSK_MACHINE=riscv64
        export VOSK_ARCHITECTURE=64bit
        ;;
esac

# Copy library to output folder
mkdir -p /io/wheelhouse/vosk-linux-${VOSK_MACHINE}${VOSK_VARIANT}
cp /opt/vosk-api/src/*.so /opt/vosk-api/src/vosk_api.h /io/wheelhouse/vosk-linux-$VOSK_MACHINE${VOSK_VARIANT}

# Build wheel
python3 -m pip install requests tqdm srt websockets wheel --break-system-packages
python3 -m pip wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
