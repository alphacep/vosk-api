#!/bin/bash

# Follows jsilva setup

ANDROID_NDK_HOME=$HOME/android/sdk/ndk-bundle
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64
WORKDIR=`pwd`/build/kaldi
PATH=$PATH:$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin
OPENFST_VERSION=1.6.7

# openblas first
mkdir -p $WORKDIR
cd $WORKDIR
git clone https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=ARMV7 ONLY_CBLAS=1 AR=arm-linux-androideabi-ar CC="armv7a-linux-androideabi21-clang" HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j4
make -C OpenBLAS install PREFIX=$WORKDIR/local

# CLAPACK since gfortran is missing
cd $WORKDIR
git clone https://github.com/simonlynen/android_libs
cd android_libs/lapack
sed -i 's/APP_STL := gnustl_static/APP_STL := c++_static/g' jni/Application.mk && \
sed -i 's/android-10/android-16/g' project.properties && \
sed -i 's/APP_ABI := armeabi armeabi-v7a/APP_ABI := armeabi-v7a /g' jni/Application.mk && \
sed -i 's/LOCAL_MODULE:= testlapack/#LOCAL_MODULE:= testlapack/g' jni/Android.mk && \
sed -i 's/LOCAL_SRC_FILES:= testclapack.cpp/#LOCAL_SRC_FILES:= testclapack.cpp/g' jni/Android.mk && \
sed -i 's/LOCAL_STATIC_LIBRARIES := lapack/#LOCAL_STATIC_LIBRARIES := lapack/g' jni/Android.mk && \
sed -i 's/include $(BUILD_SHARED_LIBRARY)/#include $(BUILD_SHARED_LIBRARY)/g' jni/Android.mk && \
${ANDROID_NDK_HOME}/ndk-build && \
cp obj/local/armeabi-v7a/*.a ${WORKDIR}/local/lib

# tools directory --> we'll only compile OpenFST
cd $WORKDIR
wget -c -T 10 -t 1 http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-${OPENFST_VERSION}.tar.gz || \
wget -c -T 10 -t 3 http://www.openslr.org/resources/2/openfst-${OPENFST_VERSION}.tar.gz

tar -zxvf openfst-${OPENFST_VERSION}.tar.gz
cd openfst-${OPENFST_VERSION}
CXX=armv7a-linux-androideabi21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --prefix=${WORKDIR}/local --enable-shared --enable-static --with-pic --disable-bin --enable-lookahead-fsts --enable-ngram-fsts --host=arm-linux-androideabi
make -j 8
make install

# Kaldi itself
cd $WORKDIR
git clone https://github.com/alphacep/kaldi
cd $WORKDIR/kaldi
git checkout android-mix
cd $WORKDIR/kaldi/src

CXX=armv7a-linux-androideabi21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
    --mathlib=OPENBLAS --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=arm-linux-androideabi --openblas-root=${WORKDIR}/local \
    --fst-root=${WORKDIR}/local --fst-version=${OPENFST_VERSION}

make depend -j
make -j 8 online2
