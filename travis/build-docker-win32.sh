#!/bin/bash

set -e -x 
docker build --file Dockerfile.win32 --tag alphacep/kaldi-win32:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-win32 /io/travis/build-wheels-win32.sh
