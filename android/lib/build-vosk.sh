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

if [ "x$ANDROID_NDK_HOME" == "x" ]; then
    echo "ANDROID_NDK_HOME environment variable is undefined, define it with local.properties or with export"
    exit 1
fi

if [ ! -d "$ANDROID_NDK_HOME" ]; then
    echo "ANDROID_NDK_HOME ($ANDROID_NDK_HOME) is missing. Make sure you have ndk installed"
    exit 1
fi

set -x

OS_NAME=`echo $(uname -s) | tr '[:upper:]' '[:lower:]'`
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64
WORKDIR_BASE=`pwd`/build
PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64/bin:$PATH
OPENFST_VERSION=1.8.0

for arch in armeabi-v7a arm64-v8a x86_64 x86; do

WORKDIR=${WORKDIR_BASE}/kaldi_${arch}

case $arch in
    armeabi-v7a)
          BLAS_ARCH=ARMV7
          HOST=arm-linux-androideabi
          AR=llvm-ar
          RANLIB=llvm-ranlib
          CC=armv7a-linux-androideabi21-clang
          CXX=armv7a-linux-androideabi21-clang++
          ARCHFLAGS="-mfloat-abi=softfp -mfpu=neon"
          ;;
    arm64-v8a)
          BLAS_ARCH=ARMV8
          HOST=aarch64-linux-android
          AR=llvm-ar
          RANLIB=llvm-ranlib
          CC=aarch64-linux-android21-clang
          CXX=aarch64-linux-android21-clang++
          ARCHFLAGS=""
          ;;
    x86_64)
          BLAS_ARCH=ATOM
          HOST=x86_64-linux-android
          AR=llvm-ar
          RANLIB=llvm-ranlib
          CC=x86_64-linux-android21-clang
          CXX=x86_64-linux-android21-clang++
          ARCHFLAGS=""
          ;;
    x86)
          BLAS_ARCH=ATOM
          HOST=i686-linux-android
          AR=llvm-ar
          RANLIB=llvm-ranlib
          CC=i686-linux-android21-clang
          CXX=i686-linux-android21-clang++
          ARCHFLAGS=""
          ;;
esac

mkdir -p $WORKDIR/local/lib

# openblas first
cd $WORKDIR
git clone -b v0.3.20 --single-branch https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=$BLAS_ARCH ONLY_CBLAS=1 AR=$AR CC=$CC HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j 8
make -C OpenBLAS install PREFIX=$WORKDIR/local

# CLAPACK
cd $WORKDIR
git clone -b v3.2.1  --single-branch https://github.com/alphacep/clapack
mkdir -p clapack/BUILD && cd clapack/BUILD
cmake -DCMAKE_C_FLAGS="$ARCHFLAGS" -DCMAKE_C_COMPILER_TARGET=$HOST \
    -DCMAKE_C_COMPILER=$CC -DCMAKE_SYSTEM_NAME=Generic -DCMAKE_AR=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/${OS_NAME}-x86_64/bin/$AR \
    -DCMAKE_TRY_COMPILE_TARGET_TYPE=STATIC_LIBRARY \
    -DCMAKE_CROSSCOMPILING=True ..
make -j 8 -C F2CLIBS/libf2c
make -j 8 -C BLAS/SRC
make -j 8 -C SRC
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
git clone -b vosk-android --single-branch https://github.com/alphacep/kaldi
cd $WORKDIR/kaldi/src
CXX=$CXX AR=$AR RANLIB=$RANLIB CXXFLAGS="$ARCHFLAGS -O3 -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
    --mathlib=OPENBLAS_CLAPACK --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=$HOST --openblas-root=${WORKDIR}/local \
    --fst-root=${WORKDIR}/local --fst-version=${OPENFST_VERSION}
make -j 8 depend
cd $WORKDIR/kaldi/src
make -j 8 online2 rnnlm

# Vosk-api
cd $WORKDIR
mkdir -p $WORKDIR/vosk
make -j 8 -C ${WORKDIR_BASE}/../../../src \
    OUTDIR=$WORKDIR/vosk \
    KALDI_ROOT=${WORKDIR}/kaldi \
    OPENFST_ROOT=${WORKDIR}/local \
    OPENBLAS_ROOT=${WORKDIR}/local \
    CXX=$CXX \
    EXTRA_LDFLAGS="-llog -static-libstdc++ -Wl,-soname,libvosk.so"
cp $WORKDIR/vosk/libvosk.so $WORKDIR/../../src/main/jniLibs/$arch/libvosk.so

done
