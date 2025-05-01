#!/bin/bash

set -e
set -x

docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-armv7l-musl" --build-arg="OPENBLAS_ARGS=TARGET=ARMV7" --file Dockerfile.dockcross-musl --tag alphacep/kaldi-dockcross-armv7-musl:latest .
docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-armv7-musl /io/travis/build-wheels-dockcross.sh
