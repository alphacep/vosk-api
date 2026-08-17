# Locations of the dependencies
KALDI_ROOT?=$(HOME)/travis/kaldi
OPENFST_ROOT?=$(KALDI_ROOT)/tools/openfst
OPENBLAS_ROOT?=$(KALDI_ROOT)/tools/OpenBLAS/install
MKL_ROOT?=/opt/intel/mkl
CUDA_ROOT?=/usr/local/cuda
USE_SHARED?=0
# Math libraries
HAVE_OPENBLAS_CLAPACK?=1
HAVE_OPENBLAS_NO_F2C?=0
HAVE_MKL?=0
HAVE_ACCELERATE=0
HAVE_CUDA?=0
# Compiler
CXX?=g++
EXT?=so
# Extra
EXTRA_CFLAGS?=
EXTRA_LDFLAGS?=
OUTDIR?=.

VOSK_SOURCES= \
	recognizer.cc \
	language_model.cc \
	model.cc \
	spk_model.cc \
	vosk_api.cc \
	postprocessor.cc

VOSK_HEADERS= \
	recognizer.h \
	language_model.h \
	model.h \
	spk_model.h \
	vosk_api.h \
        postprocessor.h

CFLAGS=-g -O3 -std=c++17 -Wno-deprecated-declarations -fPIC -DFST_NO_DYNAMIC_LINKING -I. -I$(KALDI_ROOT)/src -I$(OPENFST_ROOT)/include $(EXTRA_CFLAGS)

LDFLAGS=

ifeq ($(USE_SHARED), 0)
    LIBS = \
        $(KALDI_ROOT)/src/online2/kaldi-online2.a \
        $(KALDI_ROOT)/src/decoder/kaldi-decoder.a \
        $(KALDI_ROOT)/src/ivector/kaldi-ivector.a \
        $(KALDI_ROOT)/src/gmm/kaldi-gmm.a \
        $(KALDI_ROOT)/src/tree/kaldi-tree.a \
        $(KALDI_ROOT)/src/feat/kaldi-feat.a \
        $(KALDI_ROOT)/src/lat/kaldi-lat.a \
        $(KALDI_ROOT)/src/lm/kaldi-lm.a \
        $(KALDI_ROOT)/src/rnnlm/kaldi-rnnlm.a \
        $(KALDI_ROOT)/src/hmm/kaldi-hmm.a \
        $(KALDI_ROOT)/src/nnet3/kaldi-nnet3.a \
        $(KALDI_ROOT)/src/transform/kaldi-transform.a \
        $(KALDI_ROOT)/src/cudamatrix/kaldi-cudamatrix.a \
        $(KALDI_ROOT)/src/matrix/kaldi-matrix.a \
        $(KALDI_ROOT)/src/fstext/kaldi-fstext.a \
        $(KALDI_ROOT)/src/util/kaldi-util.a \
        $(KALDI_ROOT)/src/base/kaldi-base.a \
        $(OPENFST_ROOT)/lib/libfst.a \
        $(OPENFST_ROOT)/lib/libfstngram.a
else
    LDFLAGS += \
        -L$(KALDI_ROOT)/libs \
        -lkaldi-online2 -lkaldi-decoder -lkaldi-ivector -lkaldi-gmm -lkaldi-tree \
        -lkaldi-feat -lkaldi-lat -lkaldi-lm -lkaldi-rnnlm -lkaldi-hmm -lkaldi-nnet3 \
        -lkaldi-transform -lkaldi-cudamatrix -lkaldi-matrix -lkaldi-fstext \
        -lkaldi-util -lkaldi-base -lfst -lfstngram
endif

ifeq ($(HAVE_OPENBLAS_CLAPACK), 1)
    CFLAGS += -I$(OPENBLAS_ROOT)/include
    ifeq ($(USE_SHARED), 0)
        LIBS += \
            $(OPENBLAS_ROOT)/lib/libopenblas.a \
            $(OPENBLAS_ROOT)/lib/liblapack.a \
            $(OPENBLAS_ROOT)/lib/libblas.a \
            $(OPENBLAS_ROOT)/lib/libf2c.a
    else
        LDFLAGS += -lopenblas -llapack -lblas -lf2c
    endif
endif

ifeq ($(HAVE_OPENBLAS_NO_F2C), 1)
    CFLAGS += -I$(OPENBLAS_ROOT)/include
    ifeq ($(USE_SHARED), 0)
        LIBS += \
            $(OPENBLAS_ROOT)/lib/libopenblas.a \
            $(OPENBLAS_ROOT)/lib/liblapack.a \
            $(OPENBLAS_ROOT)/lib/libblas.a
    else
        LDFLAGS += -lopenblas -llapack -lblas
    endif
endif

ifeq ($(HAVE_MKL), 1)
    CFLAGS += -DHAVE_MKL=1 -I$(MKL_ROOT)/include
    LDFLAGS += -L$(MKL_ROOT)/lib/intel64 -Wl,-rpath=$(MKL_ROOT)/lib/intel64 -lmkl_rt -lmkl_intel_lp64 -lmkl_core -lmkl_sequential
endif

ifeq ($(HAVE_ACCELERATE), 1)
    LDFLAGS += -framework Accelerate
endif

ifeq ($(HAVE_CUDA), 1)
    VOSK_SOURCES += batch_recognizer.cc batch_model.cc
    VOSK_HEADERS += batch_recognizer.h batch_model.h

    CFLAGS+=-DHAVE_CUDA=1 -I$(CUDA_ROOT)/include

    LIBS := \
        $(KALDI_ROOT)/src/cudadecoder/kaldi-cudadecoder.a \
        $(KALDI_ROOT)/src/cudafeat/kaldi-cudafeat.a \
        $(LIBS)

    LDFLAGS += -L$(CUDA_ROOT)/lib64 -lcuda -lcublas -lcusparse -lcudart -lcurand -lcufft -lcusolver -lnvToolsExt
endif

all: $(OUTDIR)/libvosk.$(EXT)

$(OUTDIR)/libvosk.$(EXT): $(VOSK_SOURCES:%.cc=$(OUTDIR)/%.o) $(LIBS)
	$(CXX) --shared -s -o $@ $^ $(LDFLAGS) $(EXTRA_LDFLAGS)

$(OUTDIR)/%.o: %.cc $(VOSK_HEADERS)
	$(CXX) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.so *.dll
