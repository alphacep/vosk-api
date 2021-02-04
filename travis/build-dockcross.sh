#!/bin/bash

set -e
set -x

docker build --build-arg="DOCKCROSS_IMAGE=alphacep/dockcross-linux-armv7" --build-arg="OPENBLAS_ARCH=ARMV7" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-armv7:latest .
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-arm64" --build-arg="OPENBLAS_ARCH=ARMV8" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-arm64:latest .

docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-armv7 /io/travis/build-wheels-dockcross.sh
docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-arm64 /io/travis/build-wheels-dockcross.sh
