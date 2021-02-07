#!/bin/bash
set -e -x

cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
CXX=x86_64-w64-mingw32-g++-posix EXT=dll KALDI_ROOT=/opt/kaldi/kaldi OPENFST_ROOT=/opt/kaldi/local OPENBLAS_ROOT=/opt/kaldi/local make -j $(nproc)

cp /usr/lib/gcc/x86_64-w64-mingw32/*-posix/libstdc++-6.dll /opt/vosk-api/src
cp /usr/lib/gcc/x86_64-w64-mingw32/*-posix/libgcc_s_seh-1.dll /opt/vosk-api/src
cp /usr/x86_64-w64-mingw32/lib/libwinpthread-1.dll /opt/vosk-api/src

export VOSK_SOURCE=/opt/vosk-api
export VOSK_PLATFORM=Windows
export VOSK_ARCHITECTURE=64bit
python3 -m pip -v wheel /opt/vosk-api/python --no-deps -w /io/wheelhouse
