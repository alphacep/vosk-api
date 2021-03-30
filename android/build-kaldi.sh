#!/bin/bash

# Copyright 2019-2021 Alpha Cephei Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

if [ "x$ANDROID_SDK_HOME" == "x" ]; then
    echo "ANDROID_SDK_HOME environment variable is undefined, define it with local.properties or with export"
    exit 1
fi

if [ ! -d "$ANDROID_SDK_HOME" ]; then
    echo "ANDROID_SDK_HOME ($ANDROID_SDK_HOME) is missing. Make sure you have sdk installed"
    exit 1
fi

if [ ! -d "$ANDROID_SDK_HOME/ndk-bundle" ]; then
    echo "$ANDROID_SDK_HOME/ndk-bundle is missing. Make sure you have ndk installed within sdk"
    exit 1
fi

set -x

OS_NAME=`echo $(uname -s) | tr '[:upper:]' '[:lower:]'`
ANDROID_NDK_HOME=$ANDROID_SDK_HOME/ndk-bundle
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64
WORKDIR_X86=`pwd`/build/kaldi_x86
WORKDIR_X86_64=`pwd`/build/kaldi_x86_64
WORKDIR_ARM32=`pwd`/build/kaldi_arm_32
WORKDIR_ARM64=`pwd`/build/kaldi_arm_64
PATH=$PATH:$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64/bin
OPENFST_VERSION=1.8.0

for arch in arm32 arm64 x86_64 x86; do
#for arch in arm32; do

case $arch in
    arm32)
          BLAS_ARCH=ARMV7
          WORKDIR=$WORKDIR_ARM32
          HOST=arm-linux-androideabi
          AR=arm-linux-androideabi-ar
          CC=armv7a-linux-androideabi21-clang
          CXX=armv7a-linux-androideabi21-clang++
          ARCHFLAGS="-mfloat-abi=softfp -mfpu=neon"
          ;;
    arm64)
          BLAS_ARCH=ARMV8
          WORKDIR=$WORKDIR_ARM64
          HOST=aarch64-linux-android
          AR=aarch64-linux-android-ar
          CC=aarch64-linux-android21-clang
          CXX=aarch64-linux-android21-clang++
          ARCHFLAGS=""
          ;;
    x86_64)
          BLAS_ARCH=ATOM
          WORKDIR=$WORKDIR_X86_64
          HOST=x86_64-linux-android
          AR=x86_64-linux-android-ar
          CC=x86_64-linux-android21-clang
          CXX=x86_64-linux-android21-clang++
          ARCHFLAGS=""
          ;;
    x86)
          BLAS_ARCH=ATOM
          WORKDIR=$WORKDIR_X86
          HOST=i686-linux-android
          AR=i686-linux-android-ar
          CC=i686-linux-android21-clang
          CXX=i686-linux-android21-clang++
          ARCHFLAGS=""
          ;;
esac


mkdir -p $WORKDIR/local/lib

# openblas first
cd $WORKDIR
git clone -b v0.3.13 --single-branch https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=$BLAS_ARCH ONLY_CBLAS=1 AR=$AR CC=$CC HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j4
make -C OpenBLAS install PREFIX=$WORKDIR/local

# CLAPACK
cd $WORKDIR
git clone -b v3.2.1  --single-branch https://github.com/alphacep/clapack
mkdir -p clapack/BUILD && cd clapack/BUILD
cmake -DCMAKE_C_FLAGS=$ARCHFLAGS -DCMAKE_C_COMPILER_TARGET=$HOST \
    -DCMAKE_C_COMPILER=$CC -DCMAKE_SYSTEM_NAME=Generic -DCMAKE_AR=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64/bin/$AR \
    -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
    -DCMAKE_CROSSCOMPILING=True ..
make -C F2CLIBS/libf2c
make -C BLAS/SRC
make -C SRC
find . -name "*.a" | xargs cp -t $WORKDIR/local/lib

# tools directory --> we'll only compile OpenFST
cd $WORKDIR
git clone https://github.com/alphacep/openfst
cd openfst
autoreconf -i
CXX=$CXX CXXFLAGS="$ARCHFLAGS -O3 -DFST_NO_DYNAMIC_LINKING" ./configure --prefix=${WORKDIR}/local \
    --enable-shared --enable-static --with-pic --disable-bin \
    --enable-lookahead-fsts --enable-ngram-fsts --host=$HOST --build=x86-linux-gnu
make -j 8
make install

# Kaldi itself
cd $WORKDIR
git clone -b android-mix --single-branch https://github.com/alphacep/kaldi
cd $WORKDIR/kaldi/src
if [ "`uname`" == "Darwin"  ]; then
  sed -i.bak -e 's/libfst.dylib/libfst.a/' configure
fi
CXX=$CXX CXXFLAGS="$ARCHFLAGS -O3 -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
    --mathlib=OPENBLAS_CLAPACK --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=$HOST --openblas-root=${WORKDIR}/local \
    --fst-root=${WORKDIR}/local --fst-version=${OPENFST_VERSION}
make -j 8 depend
make -j 8 online2 lm

cd $WORKDIR
git clone -b master --single-branch https://github.com/alphacep/vosk-api
cd vosk-api/src
make KALDI_ROOT=${WORKDIR}/kaldi OPENFST_ROOT=${WORKDIR}/local OPENBLAS_ROOT=${WORKDIR}/local CXX=$CXX

done
