#!/bin/bash

# Copyright 2019 Alpha Cephei Inc.
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
OPENFST_VERSION=1.6.7

mkdir -p $WORKDIR_ARM64/local/lib $WORKDIR_ARM32/local/lib $WORKDIR_X86_64/local/lib $WORKDIR_X86/local/lib

# Build standalone CLAPACK since gfortran is missing
cd build
git clone https://github.com/simonlynen/android_libs
cd android_libs/lapack
sed -i.bak -e 's/APP_STL := gnustl_static/APP_STL := c++_static/g' jni/Application.mk && \
sed -i.bak -e 's/android-10/android-21/g' project.properties && \
sed -i.bak -e 's/APP_ABI := armeabi armeabi-v7a/APP_ABI := armeabi-v7a arm64-v8a x86_64 x86/g' jni/Application.mk && \
sed -i.bak -e 's/LOCAL_MODULE:= testlapack/#LOCAL_MODULE:= testlapack/g' jni/Android.mk && \
sed -i.bak -e 's/LOCAL_SRC_FILES:= testclapack.cpp/#LOCAL_SRC_FILES:= testclapack.cpp/g' jni/Android.mk && \
sed -i.bak -e 's/LOCAL_STATIC_LIBRARIES := lapack/#LOCAL_STATIC_LIBRARIES := lapack/g' jni/Android.mk && \
sed -i.bak -e 's/include $(BUILD_SHARED_LIBRARY)/#include $(BUILD_SHARED_LIBRARY)/g' jni/Android.mk && \
${ANDROID_NDK_HOME}/ndk-build && \
cp obj/local/armeabi-v7a/*.a ${WORKDIR_ARM32}/local/lib && \
cp obj/local/arm64-v8a/*.a ${WORKDIR_ARM64}/local/lib
cp obj/local/x86_64/*.a ${WORKDIR_X86_64}/local/lib
cp obj/local/x86/*.a ${WORKDIR_X86}/local/lib

# Architecture-specific part

for arch in arm32 arm64 x86_64 x86; do
#for arch in x86_64; do

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

# openblas first
cd $WORKDIR
git clone -b v0.3.7 --single-branch https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=$BLAS_ARCH ONLY_CBLAS=1 AR=$AR CC=$CC HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j4
make -C OpenBLAS install PREFIX=$WORKDIR/local

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
    --mathlib=OPENBLAS --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=$HOST --openblas-root=${WORKDIR}/local \
    --fst-root=${WORKDIR}/local --fst-version=${OPENFST_VERSION}

make -j 8 depend
make -j 8 online2 lm

done
