#!/bin/bash

set -e -x 
docker build --file Dockerfile.manylinux-mkl --tag alphacep/kaldi-manylinux-mkl:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-manylinux-mkl /io/travis/build-wheels-mkl.sh
