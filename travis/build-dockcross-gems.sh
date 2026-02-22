#!/bin/bash
set -e -x

# Build Docker images (same as build-dockcross.sh)
docker build --build-arg="DOCKCROSS_IMAGE=alphacep/dockcross-linux-armv7" --build-arg="OPENBLAS_ARGS=TARGET=ARMV7" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-armv7:latest .
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-x86" --build-arg="OPENBLAS_ARGS=TARGET=CORE2\ DYNAMIC_ARCH=1" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-x86:latest .
docker build --build-arg="DOCKCROSS_IMAGE=dockcross/linux-riscv64" --build-arg="OPENBLAS_ARGS=TARGET=RISCV64_GENERIC\ ARCH=riscv64" --file Dockerfile.dockcross --tag alphacep/kaldi-dockcross-riscv:latest .

mkdir -p ../gemhouse

# armv7l -> arm-linux gem
docker run --rm -v `realpath ..`:/io alphacep/kaldi-dockcross-armv7 /io/travis/build-gems-dockcross.sh
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Linux \
    -e VOSK_MACHINE=armv7l \
    -e VOSK_ARCHITECTURE=32bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*arm*.gem ../gemhouse/

# x86 -> x86-linux gem
docker run --rm -v `realpath ..`:/io alphacep/kaldi-dockcross-x86 /io/travis/build-gems-dockcross.sh
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Linux \
    -e VOSK_MACHINE=x86 \
    -e VOSK_ARCHITECTURE=32bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*x86*.gem ../gemhouse/

# riscv64 -> riscv64-linux gem
docker run --rm -v `realpath ..`:/io alphacep/kaldi-dockcross-riscv /io/travis/build-gems-dockcross.sh
docker run --rm \
    -v `realpath ..`:/io \
    -e VOSK_SOURCE=/io \
    -e VOSK_SYSTEM=Linux \
    -e VOSK_MACHINE=riscv64 \
    -e VOSK_ARCHITECTURE=64bit \
    ruby:3.2 \
    ruby /io/ruby/build_native_gem.rb
cp ../ruby/pkg/vosk-*riscv*.gem ../gemhouse/
