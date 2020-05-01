#!/bin/bash
set -e -x

export KALDI_ROOT=/opt/kaldi

# Compile wheels
for pypath in /opt/python/cp3[56789]*; do
    export WHEEL_FLAGS=`${pypath}/bin/python3-config --cflags`
    mkdir -p /opt/wheelhouse
    "${pypath}/bin/pip" wheel /io/python -w /opt/wheelhouse
done

# Bundle external shared libraries into the wheels
for whl in /opt/wheelhouse/*.whl; do
    auditwheel repair "$whl" --plat $PLAT -w /io/wheelhouse/
done
