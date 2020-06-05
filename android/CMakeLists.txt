# Vosk CMake File

cmake_minimum_required(VERSION 3.4.1)

if ("x${ANDROID_ABI}" STREQUAL "xarmeabi-v7a")
set(OPENBLAS_ARCH "armv7")
set(KALDI_SUFFIX "arm_32")
elseif ("x${ANDROID_ABI}" STREQUAL "xarm64-v8a")
set(OPENBLAS_ARCH "armv8")
set(KALDI_SUFFIX "arm_64")
elseif ("x${ANDROID_ABI}" STREQUAL "xx86")
set(OPENBLAS_ARCH "atom")
set(KALDI_SUFFIX "x86")
else ("x${ANDROID_ABI}" STREQUAL "xarmeabi-v7a")
set(OPENBLAS_ARCH "atom")
set(KALDI_SUFFIX "x86_64")
endif ("x${ANDROID_ABI}" STREQUAL "xarmeabi-v7a")

set(KALDI_ROOT "${PROJECT_SOURCE_DIR}/build/kaldi_${KALDI_SUFFIX}/kaldi")
set(LIB_ROOT "${PROJECT_SOURCE_DIR}/build/kaldi_${KALDI_SUFFIX}/local")

set(API_SOURCES
"${PROJECT_SOURCE_DIR}/../src/kaldi_recognizer.cc"
"${PROJECT_SOURCE_DIR}/../src/kaldi_recognizer.h"
"${PROJECT_SOURCE_DIR}/../src/model.cc"
"${PROJECT_SOURCE_DIR}/../src/model.h"
"${PROJECT_SOURCE_DIR}/../src/spk_model.cc"
"${PROJECT_SOURCE_DIR}/../src/spk_model.h"
"${PROJECT_SOURCE_DIR}/../src/vosk_api.cc"
"${PROJECT_SOURCE_DIR}/../src/vosk_api.h"
)

set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -DFST_NO_DYNAMIC_LINKING")

add_library( kaldi_jni SHARED
             build/generated-src/cpp/vosk_wrap.cc
             ${API_SOURCES}
)

include_directories("${PROJECT_SOURCE_DIR}/../src" "build/kaldi_${KALDI_SUFFIX}/kaldi/src" "build/kaldi_${KALDI_SUFFIX}/local/include")

target_link_libraries( kaldi_jni
             ${KALDI_ROOT}/src/online2/kaldi-online2.a
             ${KALDI_ROOT}/src/decoder/kaldi-decoder.a
             ${KALDI_ROOT}/src/ivector/kaldi-ivector.a
             ${KALDI_ROOT}/src/gmm/kaldi-gmm.a
             ${KALDI_ROOT}/src/nnet3/kaldi-nnet3.a
             ${KALDI_ROOT}/src/tree/kaldi-tree.a
             ${KALDI_ROOT}/src/feat/kaldi-feat.a
             ${KALDI_ROOT}/src/lat/kaldi-lat.a
             ${KALDI_ROOT}/src/lm/kaldi-lm.a
             ${KALDI_ROOT}/src/hmm/kaldi-hmm.a
             ${KALDI_ROOT}/src/transform/kaldi-transform.a
             ${KALDI_ROOT}/src/cudamatrix/kaldi-cudamatrix.a
             ${KALDI_ROOT}/src/matrix/kaldi-matrix.a
             ${KALDI_ROOT}/src/fstext/kaldi-fstext.a
             ${KALDI_ROOT}/src/util/kaldi-util.a
             ${KALDI_ROOT}/src/base/kaldi-base.a
             ${LIB_ROOT}/lib/libfst.a
             ${LIB_ROOT}/lib/libfstngram.a
             ${LIB_ROOT}/lib/libopenblas_${OPENBLAS_ARCH}-r0.3.7.a
             ${LIB_ROOT}/lib/libclapack.a
             ${LIB_ROOT}/lib/liblapack.a
             ${LIB_ROOT}/lib/libblas.a
             ${LIB_ROOT}/lib/libf2c.a
             log
             )
