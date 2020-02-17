cmake_minimum_required(VERSION 3.10.1)
project(vosk)

if("x$ENV{PYTHON_CFLAGS}" STREQUAL "x")
    find_package (Python REQUIRED COMPONENTS Development)
    message(STATUS "Python found, Python_INCLUDE_DIRS=${Python_INCLUDE_DIRS} Python_LIBRARIES=${Python_LIBRARIES}")
else()
    separate_arguments(PYTHON_CFLAGS UNIX_COMMAND $ENV{PYTHON_CFLAGS})
    add_compile_options(${PYTHON_CFLAGS})
    set(Python_INCLUDE_DIRS "")
    set(Python_LIBRARY "")
    message(STATUS "Not searching for Python, since PYTHON_CFLAGS env var is set (${PYTHON_CFLAGS})")
endif()

set(TOP_SRCDIR "$ENV{TOP_SRCDIR}")
if(NOT TOP_SRCDIR)
    set(TOP_SRCDIR "${CMAKE_SOURCE_DIR}/..")
endif()
message(STATUS "Assuming TOP_SRCDIR=${TOP_SRCDIR} contains src/vosk.i")

set(KALDI_ROOT "$ENV{KALDI_ROOT}")
if(NOT KALDI_ROOT)
    set(KALDI_ROOT "${TOP_SRCDIR}/kaldi")
endif()
message(STATUS "Looking for Kaldi in ${KALDI_ROOT}")

set(OPENBLAS_ROOT "$ENV{OPENBLAS_ROOT}")
if(NOT OPENBLAS_ROOT)
    set(OPENBLAS_ROOT "${KALDI_ROOT}/tools/OpenBLAS")
endif()
message(STATUS "Looking for OpenBLAS in ${OPENBLAS_ROOT}")

set(OPENFST_ROOT "$ENV{OPENFST_ROOT}")
if(NOT OPENFST_ROOT)
    set(OPENFST_ROOT "${KALDI_ROOT}/tools/openfst")
endif()
message(STATUS "Looking for OpenFST in ${OPENFST_ROOT}")

if(MSVC)
    add_compile_options(/W1 /wo4291 /O2 /DFST_NO_DYNAMIC_LINKING)
    set(OPENFST_INCLUDE "${OPENFST_ROOT}/src/include")
    set(VOSK_LIBRARIES
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-online2.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-decoder.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-ivector.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-gmm.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-nnet3.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-tree.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-feat.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-lat.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-hmm.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-transform.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-cudamatrix.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-matrix.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-fstext.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-util.lib
        ${KALDI_ROOT}/kaldiwin_vs2017_OPENBLAS/x64/Release/kaldi-base.lib
        ${OPENFST_ROOT}/build64/src/lib/Release/fst.lib
        ${OPENFST_ROOT}/build64/src/extensions/ngram/Release/fstngram.lib
        ${OPENBLAS_ROOT}/lib/libopenblas.lib
        ${Python_LIBRARIES}
    )
    set(MINGW_ROOT "$ENV{MINGW_ROOT}")
    set(ADDITIONAL_LIBRARIES
        ${OPENBLAS_ROOT}/bin/libopenblas.dll
        ${MINGW_ROOT}/mingw64_dll/libgcc_s_seh-1.dll
        ${MINGW_ROOT}/mingw64_dll/libgfortran-3.dll
        ${MINGW_ROOT}/mingw64_dll/libquadmath-0.dll
    )
else()
    add_compile_options(-std=c++11 -O3 -DFST_NO_DYNAMIC_LINKING
        -Wno-sign-compare
        -Wno-unused-local-typedefs
        -Wno-unused-variable
    )
    set(OPENFST_INCLUDE "${OPENFST_ROOT}/include")
    set(VOSK_LIBRARIES
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
        ${OPENFST_ROOT}/lib/libfst.a
        ${OPENFST_ROOT}/lib/libfstngram.a
        ${OPENBLAS_ROOT}/libopenblas.a
        ${Python_LIBRARIES}
        -lgfortran
    )
endif()

include_directories("${TOP_SRCDIR}/src" "${KALDI_ROOT}/src" ${OPENFST_INCLUDE} ${Python_INCLUDE_DIRS})

find_package(SWIG REQUIRED)
include(${SWIG_USE_FILE})

set_property(SOURCE "${TOP_SRCDIR}/src/vosk.i" PROPERTY CPLUSPLUS ON)
swig_add_library(vosk TYPE SHARED LANGUAGE Python OUTPUT_DIR "${CMAKE_LIBRARY_OUTPUT_DIRECTORY}" OUTFILE_DIR "."
    SOURCES "${TOP_SRCDIR}/src/kaldi_recognizer.cc" 
            "${TOP_SRCDIR}/src/spk_model.cc"
            "${TOP_SRCDIR}/src/model.cc"
            "${TOP_SRCDIR}/src/vosk.i")

swig_link_libraries(vosk ${VOSK_LIBRARIES})

if(NOT MSVC)
    set_target_properties(_vosk PROPERTIES LINK_FLAGS_RELEASE -s)
endif()

file(INSTALL ${ADDITIONAL_LIBRARIES} DESTINATION ${CMAKE_LIBRARY_OUTPUT_DIRECTORY})
