#!/bin/bash
set -e -x

export KALDI_ROOT=/opt/kaldi

# Compile wheels
for pypath in /opt/python/cp3[56789]*; do
    export VOSK_SOURCE=/io/src
    mkdir -p /opt/wheelhouse
    rm -rf /io/python/build
    "${pypath}/bin/pip" -v wheel /io/python -w /opt/wheelhouse
done

# Bundle external shared libraries into the wheels
for whl in /opt/wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done
