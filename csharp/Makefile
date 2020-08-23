KALDI_ROOT ?= $(HOME)/kaldi
CFLAGS :=  -std=c++11 -g -O2 -DPIC -fPIC -Wno-unused-function
CPPFLAGS := -I$(KALDI_ROOT)/src -I$(KALDI_ROOT)/tools/openfst/include -I../src -DFST_NO_DYNAMIC_LINKING

KALDI_LIBS = \
             ${KALDI_ROOT}/src/online2/kaldi-online2.a \
             ${KALDI_ROOT}/src/decoder/kaldi-decoder.a \
             ${KALDI_ROOT}/src/ivector/kaldi-ivector.a \
             ${KALDI_ROOT}/src/gmm/kaldi-gmm.a \
             ${KALDI_ROOT}/src/nnet3/kaldi-nnet3.a \
             ${KALDI_ROOT}/src/tree/kaldi-tree.a \
             ${KALDI_ROOT}/src/feat/kaldi-feat.a \
             ${KALDI_ROOT}/src/lat/kaldi-lat.a \
             ${KALDI_ROOT}/src/lm/kaldi-lm.a \
             ${KALDI_ROOT}/src/hmm/kaldi-hmm.a \
             ${KALDI_ROOT}/src/transform/kaldi-transform.a \
             ${KALDI_ROOT}/src/cudamatrix/kaldi-cudamatrix.a \
             ${KALDI_ROOT}/src/matrix/kaldi-matrix.a \
             ${KALDI_ROOT}/src/fstext/kaldi-fstext.a \
             ${KALDI_ROOT}/src/util/kaldi-util.a \
             ${KALDI_ROOT}/src/base/kaldi-base.a \
             ${KALDI_ROOT}/tools/openfst/lib/libfst.a \
             ${KALDI_ROOT}/tools/openfst/lib/libfstngram.a

# On Linux
MATH_LIBS = ${KALDI_ROOT}/tools/OpenBLAS/libopenblas.a -lgfortran
# On OSX
# MATH_LIBS = -framework Accelerate

all: test.exe

test.exe: libkaldiwrap.so test.cs
	mcs test.cs gen/*.cs

VOSK_SOURCES = \
	vosk_wrap.c \
	../src/kaldi_recognizer.cc \
	../src/model.cc \
	../src/spk_model.cc \
	../src/vosk_api.cc

VOSK_HEADERS = \
	../src/kaldi_recognizer.h \
	../src/model.h \
	../src/vosk_api.h \
	../src/spk_model.h

libkaldiwrap.so: $(VOSK_SOURCES) $(VOSK_HEADERS)
	$(CXX) -fpermissive $(CFLAGS) $(CPPFLAGS) -shared -o $@ $(VOSK_SOURCES) $(KALDI_LIBS) $(MATH_LIBS)

vosk_wrap.c: ../src/vosk.i
	mkdir -p gen
	swig -csharp -DSWIG_CSHARP_NO_EXCEPTION_HELPER -dllimport "libkaldiwrap" \
	    -namespace "Kaldi" -outdir gen -o vosk_wrap.c ../src/vosk.i

run: test.exe
	mono test.exe

clean:
	$(RM) *.so vosk_wrap.c *.o gen/*.cs test.exe
