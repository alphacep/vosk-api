#!/usr/bin/env bash
set -e -x

export KALDI_ROOT=/opt/kaldi

# Compile wheels
for pypath in /opt/python/cp3*; do
    if [[ $pypath == *cp34* ]]; then
        echo "Skipping building wheel for deprecated Python version ${pypath}"
        continue
    fi
    export WHEEL_FLAGS=`${pypath}/bin/python3-config --cflags`
    mkdir -p /opt/wheelhouse
    "${pypath}/bin/pip3" install auditwheel
    "${pypath}/bin/pip3" wheel /io/python -w /opt/wheelhouse

    if [[ $DEFAULT_DOCKCROSS_IMAGE == *manylinux* ]]; then
        # Bundle external shared libraries into the wheels
        "${pypath}/bin/auditwheel" repair /opt/wheelhouse/*.whl -w /io/wheelhouse
        rm /opt/wheelhouse/*.whl
    else
        # If not running on a manylinux-compatible image, we just have to hope for the best :)
        "${pypath}/bin/auditwheel" show /opt/wheelhouse/*.whl
        mv /opt/wheelhouse/*.whl /io/wheelhouse
    fi
done
