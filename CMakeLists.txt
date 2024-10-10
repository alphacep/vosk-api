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

find_package(kaldi REQUIRED)
target_link_libraries(vosk PUBLIC kaldi-base kaldi-online2 kaldi-rnnlm fstngram)

include(GNUInstallDirs)
install(TARGETS vosk DESTINATION ${CMAKE_INSTALL_LIBDIR})
install(FILES src/vosk_api.h DESTINATION ${CMAKE_INSTALL_INCLUDEDIR})
