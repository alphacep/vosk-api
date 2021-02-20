#!/bin/bash

set -e -x 
docker build --file Dockerfile.manylinux --tag alphacep/kaldi-manylinux:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-manylinux /io/travis/build-wheels.sh
