KALDI_ROOT=$(HOME)/travis/kaldi
VOSK_SOURCES=../src/kaldi_recognizer.cc ../src/model.cc ../src/spk_model.cc ../src/vosk_api.cc
CFLAGS=-g -O2 -DFST_NO_DYNAMIC_LINKING -I../src -I$(KALDI_ROOT)/src -I$(KALDI_ROOT)/tools/openfst/include
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
	$(KALDI_ROOT)/tools/OpenBLAS/libopenblas.a \
	$(KALDI_ROOT)/tools/openfst/lib/libfst.a \
	$(KALDI_ROOT)/tools/openfst/lib/libfstngram.a

test_vosk: test_vosk.o libvosk.a
	g++ $^ -o $@ $(LIBS) -lgfortran -lpthread

libvosk.a: $(VOSK_SOURCES:.cc=.o)
	ar rcs $@ $^

%.o: %.c
	g++ $(CFLAGS) -c -o $@ $<

%.o: %.cc
	g++ -std=c++11 $(CFLAGS) -c -o $@ $<

clean:
	rm -f *.o *.a test_vosk
