KALDI_ROOT=$(HOME)/travis/kaldi
EXT=so
CXX=g++
VOSK_SOURCES= \
    kaldi_recognizer.cc \
    language_model.cc \
    model.cc \
    spk_model.cc \
    vosk_api.cc

CFLAGS=-g -O2 -std=c++17 -fPIC -DFST_NO_DYNAMIC_LINKING -I. -I$(KALDI_ROOT)/src -I$(KALDI_ROOT)/tools/openfst/include
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
	$(KALDI_ROOT)/src/hmm/kaldi-hmm.a \
	$(KALDI_ROOT)/src/transform/kaldi-transform.a \
	$(KALDI_ROOT)/src/cudamatrix/kaldi-cudamatrix.a \
	$(KALDI_ROOT)/src/matrix/kaldi-matrix.a \
	$(KALDI_ROOT)/src/fstext/kaldi-fstext.a \
	$(KALDI_ROOT)/src/util/kaldi-util.a \
	$(KALDI_ROOT)/src/base/kaldi-base.a \
	$(KALDI_ROOT)/tools/OpenBLAS/install/lib/libopenblas.a \
	$(KALDI_ROOT)/tools/OpenBLAS/install/lib/liblapack.a \
	$(KALDI_ROOT)/tools/OpenBLAS/install/lib/libblas.a \
	$(KALDI_ROOT)/tools/OpenBLAS/install/lib/libf2c.a \
	$(KALDI_ROOT)/tools/openfst/lib/libfst.a \
	$(KALDI_ROOT)/tools/openfst/lib/libfstngram.a

all: libvosk.$(EXT)

libvosk.$(EXT): $(VOSK_SOURCES:.cc=.o)
	$(CXX) --shared -o $@ $^ $(LIBS) -lm -latomic

%.o: %.cc
	$(CXX) $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.so *.dll
