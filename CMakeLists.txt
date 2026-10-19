cmake_minimum_required(VERSION 3.13)
project(vosk-api CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_EXTENSIONS OFF)

add_library(vosk
  src/language_model.cc
  src/model.cc
  src/recognizer.cc
  src/spk_model.cc
  src/vosk_api.cc
  src/postprocessor.cc
)

if(BuildForFedora)
    # Version used used by Fedora 41 is 1.83
    # TODO: Detect the right version and put it here.
    add_definitions(-DOPENFST_VER=18300)
    find_package(kaldi REQUIRED)

    # Small Hack for FindKaldi that does not provide the include directory
    set(kaldi_INCLUDE_DIRS "${kaldi_DIR}/../../../include")
    target_include_directories(vosk PUBLIC ${kaldi_INCLUDE_DIRS} "${kaldi_DIR}/../../../include/kaldi")

    include_directories(/usr/include)
endif()

target_link_libraries(vosk PUBLIC kaldi-base kaldi-online2 kaldi-rnnlm fstngram)

include(GNUInstallDirs)
install(TARGETS vosk DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES src/vosk_api.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
