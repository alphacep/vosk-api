#!/usr/bin/env bash
set -e -x

export KALDI_ROOT=/opt/kaldi

# Compile wheels
for pypath in /opt/python/cp3*; do
    export WHEEL_FLAGS=`${pypath}/bin/python3-config --cflags`
    mkdir -p /opt/wheelhouse
    "${pypath}/bin/pip3" install auditwheel
    "${pypath}/bin/pip3" wheel /io/python -w /opt/wheelhouse

    if [[ $DEFAULT_DOCKCROSS_IMAGE == *manylinux* ]]; then
        # Bundle external shared libraries into the wheels
        "${pypath}/bin/auditwheel" repair /opt/wheelhouse/*.whl -w /io/wheelhouse
    else
        # If not running on a manylinux-compatible image, we just have to hope for the best :)
        "${pypath}/bin/auditwheel" show /opt/wheelhouse/*.whl
        cp /opt/wheelhouse/*.whl /io/wheelhouse
    fi
done
