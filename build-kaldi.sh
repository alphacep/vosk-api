#!/bin/bash

# Follows jsilva setup

ANDROID_NDK_HOME=$HOME/android/sdk/ndk-bundle
ANDROID_TOOLCHAIN_PATH=$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64
WORKDIR32=`pwd`/build/kaldi32
WORKDIR64=`pwd`/build/kaldi64
PATH=$PATH:$ANDROID_NDK_HOME/toolchains/llvm/prebuilt/linux-x86_64/bin
OPENFST_VERSION=1.6.7

mkdir -p $WORKDIR32/local/lib
mkdir -p $WORKDIR64/local/lib

# CLAPACK since gfortran is missing
cd $WORKDIR32
git clone https://github.com/simonlynen/android_libs
cd android_libs/lapack
sed -i 's/APP_STL := gnustl_static/APP_STL := c++_static/g' jni/Application.mk && \
sed -i 's/android-10/android-16/g' project.properties && \
sed -i 's/APP_ABI := armeabi armeabi-v7a/APP_ABI := armeabi-v7a arm64-v8a/g' jni/Application.mk && \
sed -i 's/LOCAL_MODULE:= testlapack/#LOCAL_MODULE:= testlapack/g' jni/Android.mk && \
sed -i 's/LOCAL_SRC_FILES:= testclapack.cpp/#LOCAL_SRC_FILES:= testclapack.cpp/g' jni/Android.mk && \
sed -i 's/LOCAL_STATIC_LIBRARIES := lapack/#LOCAL_STATIC_LIBRARIES := lapack/g' jni/Android.mk && \
sed -i 's/include $(BUILD_SHARED_LIBRARY)/#include $(BUILD_SHARED_LIBRARY)/g' jni/Android.mk && \
${ANDROID_NDK_HOME}/ndk-build && \
cp obj/local/armeabi-v7a/*.a ${WORKDIR32}/local/lib && \
cp obj/local/arm64-v8a/*.a ${WORKDIR64}/local/lib

# openblas first
cd $WORKDIR32
git clone https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=ARMV7 ONLY_CBLAS=1 AR=arm-linux-androideabi-ar CC="armv7a-linux-androideabi21-clang" HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j4
make -C OpenBLAS install PREFIX=$WORKDIR32/local

cd $WORKDIR64
git clone https://github.com/xianyi/OpenBLAS
make -C OpenBLAS TARGET=ARMV8 ONLY_CBLAS=1 AR=aarch64-linux-android-ar CC="aarch64-linux-android21-clang" HOSTCC=gcc ARM_SOFTFP_ABI=1 USE_THREAD=0 NUM_THREADS=1 -j4
make -C OpenBLAS install PREFIX=$WORKDIR64/local

# tools directory --> we'll only compile OpenFST
cd $WORKDIR32
wget -c -T 10 -t 1 http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-${OPENFST_VERSION}.tar.gz || \
wget -c -T 10 -t 3 http://www.openslr.org/resources/2/openfst-${OPENFST_VERSION}.tar.gz

tar -zxvf openfst-${OPENFST_VERSION}.tar.gz
cd openfst-${OPENFST_VERSION}
CXX=armv7a-linux-androideabi21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --prefix=${WORKDIR32}/local --enable-shared --enable-static --with-pic --disable-bin --enable-lookahead-fsts --enable-ngram-fsts --host=arm-linux-androideabi
make -j 8
make install

cd $WORKDIR64
wget -c -T 10 -t 1 http://www.openfst.org/twiki/pub/FST/FstDownload/openfst-${OPENFST_VERSION}.tar.gz || \
wget -c -T 10 -t 3 http://www.openslr.org/resources/2/openfst-${OPENFST_VERSION}.tar.gz

tar -zxvf openfst-${OPENFST_VERSION}.tar.gz
cd openfst-${OPENFST_VERSION}
CXX=aarch64-linux-android21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --prefix=${WORKDIR64}/local --enable-shared --enable-static --with-pic --disable-bin --enable-lookahead-fsts --enable-ngram-fsts --host=aarch64-linux-android
make -j 8
make install

# Kaldi itself
cd $WORKDIR32
git clone -b android-mix --single-branch https://github.com/alphacep/kaldi
cd $WORKDIR32/kaldi/src

CXX=armv7a-linux-androideabi21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
    --mathlib=OPENBLAS --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=arm-linux-androideabi --openblas-root=${WORKDIR32}/local \
    --fst-root=${WORKDIR32}/local --fst-version=${OPENFST_VERSION}

make -j 8 depend
make -j 8 online2

cd $WORKDIR64
git clone -b android-mix --single-branch https://github.com/alphacep/kaldi
cd $WORKDIR64/kaldi/src

CXX=aarch64-linux-android21-clang++ CXXFLAGS="-O3 -mfpu=neon -ftree-vectorize -DFST_NO_DYNAMIC_LINKING" ./configure --use-cuda=no \
    --mathlib=OPENBLAS --shared \
    --android-incdir=${ANDROID_TOOLCHAIN_PATH}/sysroot/usr/include \
    --host=aarch64-linux-android --openblas-root=${WORKDIR64}/local \
    --fst-root=${WORKDIR64}/local --fst-version=${OPENFST_VERSION}

make -j 8 depend
make -j 8 online2
