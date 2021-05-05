KALDI_ROOT?=$(HOME)/travis/kaldi
OPENFST_ROOT?=$(KALDI_ROOT)/tools/openfst
OPENBLAS_ROOT?=$(KALDI_ROOT)/tools/OpenBLAS/install
HAVE_CUDA?=0
CUDA_ROOT?=/usr/local/cuda
EXT?=so
CXX?=g++
HAVE_OPENBLAS_CLAPACK=1
HAVE_ACCELERATE=0
EXTRA_CFLGAS?=
EXTRA_LDFLAGS?=

VOSK_SOURCES= \
	kaldi_recognizer.cc \
	language_model.cc \
	model.cc \
	spk_model.cc \
	vosk_api.cc

CFLAGS=-g -O2 -std=c++17 -fPIC -DFST_NO_DYNAMIC_LINKING $(EXTRA_CFLAGS) \
	-I. -I$(KALDI_ROOT)/src -I$(OPENFST_ROOT)/include -I$(OPENBLAS_ROOT)/include

LIBS= \
	$(KALDI_ROOT)/src/online2/kaldi-online2.a \
	$(KALDI_ROOT)/src/decoder/kaldi-decoder.a \
	$(KALDI_ROOT)/src/ivector/kaldi-ivector.a \
	$(KALDI_ROOT)/src/gmm/kaldi-gmm.a \
	$(KALDI_ROOT)/src/nnet3/kaldi-nnet3.a \
	$(KALDI_ROOT)/src/tree/kaldi-tree.a \
	$(KALDI_ROOT)/src/feat/kaldi-feat.a \
	$(KALDI_ROOT)/src/lat/kaldi-lat.a \
	$(KALDI_ROOT)/src/lm/kaldi-lm.a \
	$(KALDI_ROOT)/src/rnnlm/kaldi-rnnlm.a \
	$(KALDI_ROOT)/src/hmm/kaldi-hmm.a \
	$(KALDI_ROOT)/src/transform/kaldi-transform.a \
	$(KALDI_ROOT)/src/cudamatrix/kaldi-cudamatrix.a \
	$(KALDI_ROOT)/src/matrix/kaldi-matrix.a \
	$(KALDI_ROOT)/src/fstext/kaldi-fstext.a \
	$(KALDI_ROOT)/src/util/kaldi-util.a \
	$(KALDI_ROOT)/src/base/kaldi-base.a \
	$(OPENFST_ROOT)/lib/libfst.a \
	$(OPENFST_ROOT)/lib/libfstngram.a


ifeq ($(HAVE_OPENBLAS_CLAPACK), 1)
LIBS += \
	$(OPENBLAS_ROOT)/lib/libopenblas.a \
	$(OPENBLAS_ROOT)/lib/liblapack.a \
	$(OPENBLAS_ROOT)/lib/libblas.a \
	$(OPENBLAS_ROOT)/lib/libf2c.a
endif

ifeq ($(HAVE_ACCELERATE), 1)
LIBS += \
	-framework Accelerate
endif

ifeq ($(HAVE_CUDA), 1)
CFLAGS+=-DHAVE_CUDA=1 -I$(CUDA_ROOT)/include
LIBS+=-L$(CUDA_ROOT)/lib64 -lcublas -lcusparse -lcudart -lcurand -lcufft -lcusolver -lnvToolsExt
endif

all: libvosk.$(EXT)

libvosk.$(EXT): $(VOSK_SOURCES:.cc=.o)
	$(CXX) --shared -s -o $@ $^ $(LIBS) -lm -latomic $(EXTRA_LDFLAGS)

%.o: %.cc
	$(CXX) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.so *.dll
