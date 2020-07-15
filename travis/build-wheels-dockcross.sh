#!/bin/bash
set -e -x

ORIG_PATH=$PATH
for pyver in 3.6 3.7 3.8; do

    export KALDI_ROOT=/opt/kaldi
    export PATH=/opt/python/cp${pyver}-cp${pyver}m/bin:$ORIG_PATH
    export VOSK_SOURCE=/io/src

    # Python 3.8 somehow changed syconfig file name
    sysconfig_bit="m"
    if [ $pyver == "3.8" ]; then
         sysconfig_bit=""
    fi

    case $CROSS_TRIPLE in
        *arm-*)
            export _PYTHON_HOST_PLATFORM=linux-armv6l
            export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata_${sysconfig_bit}_linux_arm-linux-gnueabihf
            ;;
        *armv7-*)
            export _PYTHON_HOST_PLATFORM=linux-armv7l
            export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata_${sysconfig_bit}_linux_arm-linux-gnueabihf
            ;;
        *aarch64-*)
            export _PYTHON_HOST_PLATFORM=linux-aarch64
            export _PYTHON_SYSCONFIGDATA_NAME=_sysconfigdata_${sysconfig_bit}_linux_aarch64-linux-gnu
            ;;
    esac
    export PYTHONHOME=$CROSS_ROOT
    export PYTHONPATH=/opt/python/cp${pyver}-cp${pyver}m/lib/python${pyver}/site-packages:/opt/python/cp${pyver}-cp${pyver}m/lib/python${pyver}/lib-dynload

    rm -rf /io/python/build
    pip${pyver} -v wheel /io/python -w /io/wheelhouse

done
