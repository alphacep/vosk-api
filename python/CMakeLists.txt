cmake_minimum_required(VERSION 3.10.1)

project(vosk)

find_package (Python COMPONENTS Interpreter Development)

set(KALDI_ROOT "$ENV{HOME}/kaldi")
set(CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} -O3 -DFST_NO_DYNAMIC_LINKING")
include_directories("../src" "${KALDI_ROOT}/src" "${KALDI_ROOT}/tools/openfst/include" ${Python_INCLUDE_DIR})

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set_property(SOURCE "../src/vosk.i" PROPERTY CPLUSPLUS ON)
swig_add_library(vosk TYPE SHARED LANGUAGE Python OUTPUT_DIR "../../vosk" OUTFILE_DIR "."
    SOURCES "../../../src/kaldi_recognizer.cc" "../src/vosk.i" "../../../src/model.cc")

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
             ${Python_LIBRARY} -lgfortran)
