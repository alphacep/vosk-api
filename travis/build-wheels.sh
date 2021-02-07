#!/bin/bash
set -e -x

cd /opt
git clone https://github.com/alphacep/vosk-api
cd vosk-api/src
KALDI_ROOT=/opt/kaldi OPENFST_ROOT=/opt/kaldi/tools/openfst OPENBLAS_ROOT=/opt/kaldi/tools/OpenBLAS/install make -j $(nproc)

mkdir -p /opt/wheelhouse
export VOSK_SOURCE=/opt/vosk-api
/opt/python/cp37*/bin/pip -v wheel /opt/vosk-api/python --no-deps -w /opt/wheelhouse

for whl in /opt/wheelhouse/*.whl; do
    cp $whl /io/wheelhouse
    auditwheel repair "$whl" --plat manylinux2010_x86_64 -w /io/wheelhouse
done
