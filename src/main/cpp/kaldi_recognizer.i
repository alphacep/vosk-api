%module kaldi_recognizer

%include <typemaps.i>
%include <std_string.i>

#if SWIGPYTHON
%include <pybuffer.i>
#endif

#if SWIGJAVA
%include <various.i>
#endif

namespace kaldi {
}

#if SWIGPYTHON
%pybuffer_binary(const char *data, int len);
#endif

#if SWIGJAVA
%apply char *BYTE {const char *data};
#endif

%{
#include "kaldi_recognizer.h"
#include "model.h"
%}

#if SWIGJAVA
%typemap(javaimports) KaldiRecognizer %{
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
%}
%typemap(javacode) KaldiRecognizer %{
  public boolean AcceptWaveform(byte[] data) {
    return AcceptWaveform(data, data.length);
  }

  public boolean AcceptWaveform(short[] data, int len) {
    byte[] bdata = new byte[len * 2];
    ByteBuffer.wrap(bdata).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().put(data, 0, len);
    return AcceptWaveform(bdata, bdata.length);
  }
%}
#endif

%include "kaldi_recognizer.h"
%include "model.h"
