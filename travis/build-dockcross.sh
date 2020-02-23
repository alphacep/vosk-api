#!/bin/bash

set -e
set -x

docker build --build-arg="DOCKCROSS_IMAGE=linux-armv7" --build-arg="OPENBLAS_ARCH=ARMV7" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-armv7:latest .
docker build --build-arg="DOCKCROSS_IMAGE=linux-armv6" --build-arg="OPENBLAS_ARCH=ARMV6" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-armv6:latest .
docker build --build-arg="DOCKCROSS_IMAGE=linux-arm64" --build-arg="OPENBLAS_ARCH=ARMV8" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-arm64:latest .
