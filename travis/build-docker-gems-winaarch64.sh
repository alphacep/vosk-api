#!/bin/bash
set -e -x

docker build --file Dockerfile.winaarch64 --tag alphacep/kaldi-winaarch64:latest .
docker run --rm -v `realpath ..`:/io alphacep/kaldi-winaarch64 /io/travis/build-gems-winaarch64.sh

mkdir -p ../gemhouse
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Windows \
    -e VOSK_MACHINE=aarch64 \
    -e VOSK_ARCHITECTURE=64bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*.gem ../gemhouse/
