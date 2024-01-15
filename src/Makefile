# ONNX
ONNX_ROOT=$(abspath ../../onnxruntime-linux-x64-1.16.3)
# Compiler
CXX?=g++
EXT?=so
# Extra
EXTRA_CFLAGS?=
EXTRA_LDFLAGS?=
OUTDIR?=.

VOSK_SOURCES= \
	circular-buffer.cc \
	context-graph.cc \
	feature-fbank.cc \
	feature-functions.cc \
	features.cc \
	feature-window.cc \
	fftsg.cc \
	file-utils.cc \
	hypothesis.cc \
	log.cc \
	mel-computations.cc \
	offline-lm.cc \
	offline-lm-config.cc \
	offline-model-config.cc \
	offline-recognizer.cc \
	offline-recognizer-impl.cc \
	offline-rnn-lm.cc \
	offline-stream.cc \
	offline-transducer-greedy-search-decoder.cc \
	offline-transducer-model.cc \
	offline-transducer-model-config.cc \
	offline-transducer-modified-beam-search-decoder.cc \
	online-feature.cc \
	onnx-utils.cc \
	packed-sequence.cc \
	pad-sequence.cc \
	parse-options.cc \
	provider.cc \
	resample.cc \
	rfft.cc \
	session.cc \
	silero-vad-model.cc \
	silero-vad-model-config.cc \
	slice.cc \
	symbol-table.cc \
	text-utils.cc \
	transpose.cc \
	utils.cc \
	vad-model.cc \
	vad-model-config.cc \
	voice-activity-detector.cc \
	vosk_api.cc

VOSK_HEADERS= \
	circular-buffer.h \
	context-graph.h \
	feature-fbank.h \
	feature-functions.h \
	features.h \
	feature-window.h \
	file-utils.h \
	hypothesis.h \
	log.h \
	macros.h \
	math.h \
	mel-computations.h \
	offline-lm-config.h \
	offline-lm.h \
	offline-model-config.h \
	offline-recognizer.h \
	offline-recognizer-impl.h \
	offline-recognizer-transducer-impl.h \
	offline-rnn-lm.h \
	offline-stream.h \
	offline-transducer-decoder.h \
	offline-transducer-greedy-search-decoder.h \
	offline-transducer-model-config.h \
	offline-transducer-model.h \
	offline-transducer-modified-beam-search-decoder.h \
	online-feature.h \
	onnx-utils.h \
	packed-sequence.h \
	pad-sequence.h \
	parse-options.h \
	provider.h \
	resample.h \
	rfft.h \
	session.h \
	silero-vad-model-config.h \
	silero-vad-model.h \
	slice.h \
	symbol-table.h \
	text-utils.h \
	transpose.h \
	utils.h \
	vad-model-config.h \
	vad-model.h \
	voice-activity-detector.h \
	vosk_api.h

CFLAGS=-g -O3 -fPIC -std=c++17 \
       -I$(ONNX_ROOT)/include $(EXTRA_CFLAGS)

LDFLAGS=-Wl,-rpath=$(ONNX_ROOT)/lib -L$(ONNX_ROOT)/lib -lonnxruntime 

all: $(OUTDIR)/libvosk.$(EXT)

$(OUTDIR)/libvosk.$(EXT): $(VOSK_SOURCES:%.cc=$(OUTDIR)/%.o)
	$(CXX) --shared -s -o $@ $^ $(LDFLAGS) $(EXTRA_LDFLAGS)

$(OUTDIR)/%.o: %.cc $(VOSK_HEADERS)
	$(CXX) -c -o $@ $(CFLAGS) $<

clean:
	rm -f *.o *.so *.dll
