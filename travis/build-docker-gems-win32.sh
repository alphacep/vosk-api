#!/bin/bash
set -e -x

docker build --file Dockerfile.win32 --tag alphacep/kaldi-win32:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-win32 /io/travis/build-gems-win32.sh

mkdir -p ../gemhouse
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Windows \
    -e VOSK_MACHINE=x86 \
    -e VOSK_ARCHITECTURE=32bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*.gem ../gemhouse/
