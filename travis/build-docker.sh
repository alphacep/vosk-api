#!/bin/bash

set -e
set -x

docker build --file Dockerfile.manylinux --tag alphacep/kaldi-manylinux:latest .
docker run --rm -e PLAT=manylinux2010_x86_64 -v /home/shmyrev/travis/vosk-api/:/io alphacep/kaldi-manylinux /io/travis/build-wheels.sh
