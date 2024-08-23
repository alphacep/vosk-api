#!/bin/bash

set -e -x 
docker build --file Dockerfile.winaarch64 --tag alphacep/kaldi-winaarch64:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-winaarch64 /io/travis/build-wheels-winaarch64.sh
