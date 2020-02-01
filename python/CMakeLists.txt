cmake_minimum_required(VERSION 3.10.1)
project(vosk)

set(TOP_SRCDIR "${CMAKE_SOURCE_DIR}/..")
if("x$ENV{WHEEL_FLAGS}" STREQUAL "x")
    find_package (Python COMPONENTS Interpreter Development)
else()
    # docker case
    set(Python_INCLUDE_DIR "")
    set(Python_LIBRARY "")
    set(TOP_SRCDIR "/io")
endif()

set(KALDI_ROOT "$ENV{KALDI_ROOT}")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -std=c++11 -O3 -DFST_NO_DYNAMIC_LINKING")
include_directories("${TOP_SRCDIR}/src" "${KALDI_ROOT}/src" "${KALDI_ROOT}/tools/openfst/include" ${Python_INCLUDE_DIR})
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} $ENV{WHEEL_FLAGS}")

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set_property(SOURCE "${TOP_SRCDIR}/src/vosk.i" PROPERTY CPLUSPLUS ON)
swig_add_library(vosk TYPE SHARED LANGUAGE Python OUTPUT_DIR "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}" OUTFILE_DIR "."
    SOURCES "${TOP_SRCDIR}/src/kaldi_recognizer.cc" "${TOP_SRCDIR}/src/vosk.i" "${TOP_SRCDIR}/src/model.cc")

swig_link_libraries(vosk
             ${KALDI_ROOT}/src/online2/kaldi-online2.a
             ${KALDI_ROOT}/src/decoder/kaldi-decoder.a
             ${KALDI_ROOT}/src/ivector/kaldi-ivector.a
             ${KALDI_ROOT}/src/gmm/kaldi-gmm.a
             ${KALDI_ROOT}/src/nnet3/kaldi-nnet3.a
             ${KALDI_ROOT}/src/tree/kaldi-tree.a
             ${KALDI_ROOT}/src/feat/kaldi-feat.a
             ${KALDI_ROOT}/src/lat/kaldi-lat.a
             ${KALDI_ROOT}/src/hmm/kaldi-hmm.a
             ${KALDI_ROOT}/src/transform/kaldi-transform.a
             ${KALDI_ROOT}/src/cudamatrix/kaldi-cudamatrix.a
             ${KALDI_ROOT}/src/matrix/kaldi-matrix.a
             ${KALDI_ROOT}/src/fstext/kaldi-fstext.a
             ${KALDI_ROOT}/src/util/kaldi-util.a
             ${KALDI_ROOT}/src/base/kaldi-base.a
             ${KALDI_ROOT}/tools/openfst/lib/libfst.a
             ${KALDI_ROOT}/tools/openfst/lib/libfstngram.a
             ${KALDI_ROOT}/tools/OpenBLAS/libopenblas.a
             -lgfortran)

set_target_properties(_vosk PROPERTIES LINK_FLAGS_RELEASE -s)
