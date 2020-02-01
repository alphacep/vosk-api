#!/usr/bin/env bash
set -e -x

export KALDI_ROOT=/opt/kaldi

# Compile wheels
for pypath in /opt/python/cp3*; do
    if [[ $pypath == *cp34* ]]; then
        echo "Skipping building wheel for deprecated Python version ${pypath}"
        continue
    fi
    export PYTHON_CFLAGS=$(${pypath}/bin/python3-config --cflags)
    export TOP_SRCDIR=/io
    mkdir -p /opt/wheelhouse
    mkdir -p /io/wheelhouse

    # use _PYTHON_HOST_PLATFORM to tell distutils.util.get_platform() the actual platform
    case $DEFAULT_DOCKCROSS_IMAGE in
        *linux-armv6*)
            export _PYTHON_HOST_PLATFORM=linux-armv6l
    esac

    "${pypath}/bin/pip3" install --upgrade auditwheel
    "${pypath}/bin/pip3" wheel /io/python -w /opt/wheelhouse -v

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
