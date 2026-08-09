#!/bin/bash
set -e -x

# Stage 1: Build native lib inside the manylinux image (same as build-docker.sh)
# This ensures glibc compat (manylinux2010 = glibc 2.12+)
docker build --file Dockerfile.manylinux --tag alphacep/kaldi-manylinux:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-manylinux /io/travis/build-gems-native.sh

# Stage 2: Package the gem using the official Ruby image.
# The .so built in stage 1 was copied to /io/src/ so build_native_gem.rb
# finds it via VOSK_SOURCE=/io -> src/*.so
mkdir -p ../gemhouse
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Linux \
    -e VOSK_MACHINE=x86_64 \
    -e VOSK_ARCHITECTURE=64bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*.gem ../gemhouse/
