#!/bin/bash
set -e -x

# Build libvosk
cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
EXTRA_LDFLAGS="-ltcmalloc_minimal" KALDI_ROOT=/opt/kaldi OPENFST_ROOT=/opt/kaldi/tools/openfst HAVE_MKL=1 HAVE_OPENBLAS_CLAPACK=0 make -j $(nproc)

# Copy dlls to output folder
mkdir -p /io/wheelhouse/vosk-linux-x86_64-mkl
cp /opt/vosk-api/src/*.so /opt/vosk-api/src/vosk_api.h /io/wheelhouse/vosk-linux-x86_64-mkl

# Build wheel and put to the output folder
mkdir -p /opt/wheelhouse
export VOSK_SOURCE=/opt/vosk-api
/opt/python/cp37*/bin/pip -v wheel /opt/vosk-api/python --no-deps -w /opt/wheelhouse

# Fix manylinux
for whl in /opt/wheelhouse/*.whl; do
    cp $whl /io/wheelhouse
    auditwheel repair "$whl" --plat manylinux2010_x86_64 -w /io/wheelhouse
done
