#!/bin/bash
set -e -x

# Stage 1: Build libvosk.dll inside the Windows cross-compile image (same as build-docker-win.sh)
docker build --file Dockerfile.win --tag alphacep/kaldi-win:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-win /io/travis/build-gems-win.sh

# Stage 2: Package the gem using the official Ruby image.
# The .dll files built in stage 1 were copied to /io/src/
mkdir -p ../gemhouse
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Windows \
    -e VOSK_MACHINE=x86_64 \
    -e VOSK_ARCHITECTURE=64bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*.gem ../gemhouse/
