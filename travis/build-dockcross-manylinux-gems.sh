#!/bin/bash
set -e -x

# Build Docker image (same as build-dockcross-manylinux.sh)
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/manylinux2014-aarch64" --build-arg="OPENBLAS_ARGS=TARGET=ARMV8" --file Dockerfile.dockcross-manylinux --tag alphacep/kaldi-dockcross-aarch64:latest .

mkdir -p ../gemhouse

# aarch64 -> aarch64-linux gem
docker run --rm -v `realpath ..`:/io alphacep/kaldi-dockcross-aarch64 /io/travis/build-gems-dockcross.sh
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Linux \
    -e VOSK_MACHINE=aarch64 \
    -e VOSK_ARCHITECTURE=64bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*aarch64*.gem ../gemhouse/
