#!/bin/bash
set -e -x

cd /opt
git clone https://github.com/alphacep/vosk-api
cd /opt/vosk-api/src
KALDI_ROOT=/opt/kaldi make -j $(nproc)

export VOSK_SOURCE=/opt/vosk-api
case $CROSS_TRIPLE in
    *armv7-*)
        export VOSK_ARCHITECTURE=armv7l
        ;;
    *aarch64-*)
        export VOSK_ARCHITECTURE=aarch64
        ;;
esac
pip3 wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
