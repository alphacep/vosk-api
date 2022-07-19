#!/bin/bash

set -e
set -x

docker build --build-arg="DOCKCROSS_IMAGE=alphacep/dockcross-linux-armv7" --build-arg="OPENBLAS_ARGS=TARGET=ARMV7" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-armv7:latest .
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-x86" --build-arg="OPENBLAS_ARGS=TARGET=CORE2\ DYNAMIC_ARCH=1" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-x86:latest .
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-riscv64" --build-arg="OPENBLAS_ARGS=TARGET=RISCV64_GENERIC\ ARCH=riscv64" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-riscv:latest .

docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-armv7 /io/travis/build-wheels-dockcross.sh
docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-x86 /io/travis/build-wheels-dockcross.sh
docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-riscv /io/travis/build-wheels-dockcross.sh

# We use manylinux (Centos-based image) for aarch64 instead
# docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-arm64" --build-arg="OPENBLAS_ARGS=TARGET=ARMV8" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-arm64:latest .
# docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-arm64 /io/travis/build-wheels-dockcross.sh
