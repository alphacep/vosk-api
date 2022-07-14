#!/bin/bash

set -e
set -x

docker build --build-arg="DOCKCROSS_IMAGE=dockcross/manylinux2014-aarch64" --build-arg="OPENBLAS_ARGS=TARGET=ARMV8" --file Dockerfile.dockcross-manylinux --tag alphacep/kaldi-dockcross-aarch64:latest .
docker run --rm -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-dockcross-aarch64 /io/travis/build-wheels-dockcross.sh
