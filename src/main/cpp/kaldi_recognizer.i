%module kaldi_recognizer

%include <typemaps.i>
%include <std_string.i>

#if SWIGPYTHON
%include <pybuffer.i>
#endif
#if SWIGJAVA
%include <arrays_java.i>
#endif

namespace kaldi {
}

#if SWIGPYTHON
%pybuffer_binary(const char *data, int len);
#endif
#if SWIGJAVA
%apply short[] {const char *data};
#endif

%{
#include "kaldi_recognizer.h"
#include "model.h"
%}

%include "kaldi_recognizer.h"
%include "model.h"

