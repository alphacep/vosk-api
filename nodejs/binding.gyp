{
  'targets': [
    {
      'target_name': 'vosk',
      'sources': [
         '../src/kaldi_recognizer.cc',
         '../src/model.cc',
         '../src/spk_model.cc',
         '../src/vosk_api.cc',
         'vosk_wrap.cc',
      ],
      'cflags': [
          '-std=c++11',
          '-DFST_NO_DYNAMIC_LINKING',
          '-Wno-deprecated-declarations',
          '-Wno-sign-compare',
          '-Wno-unused-local-typedefs',
          '-Wno-ignored-quaifiers',
          '-Wno-extra',
      ],
      'cflags_cc!' : [
          '-fno-rtti',
          '-fno-exceptions',
      ],
      'conditions': [
          ['OS == "mac"', {
              'xcode_settings': {
                  'GCC_ENABLE_CPP_EXCEPTIONS': 'YES',
                  'GCC_ENABLE_CPP_RTTI': 'YES',
                  'CLANG_CXX_LANGUAGE_STANDARD': 'c++11'
              }
          }]
      ],
      'actions': [
        {
          'action_name': 'swig',
          'inputs': [
            '../src/vosk.i',
          ],
          'outputs': [
            'vosk_wrap.cc',
          ],
          'action': ['swig', '-c++', '-javascript', '-o', 'vosk_wrap.cc', '-v8', '-DV8_MAJOR_VERSION=10', '../src/vosk.i']
        },
      ],
      'include_dirs': [
         '<@(kaldi_root)/src',
         '<@(kaldi_root)/tools/openfst/include',
         '../src',
      ],
      'link_settings': {
         'libraries': [
             '<@(kaldi_root)/src/online2/kaldi-online2.a',
             '<@(kaldi_root)/src/decoder/kaldi-decoder.a',
             '<@(kaldi_root)/src/ivector/kaldi-ivector.a',
             '<@(kaldi_root)/src/gmm/kaldi-gmm.a',
             '<@(kaldi_root)/src/nnet3/kaldi-nnet3.a',
             '<@(kaldi_root)/src/tree/kaldi-tree.a',
             '<@(kaldi_root)/src/feat/kaldi-feat.a',
             '<@(kaldi_root)/src/lat/kaldi-lat.a',
             '<@(kaldi_root)/src/lm/kaldi-lm.a',
             '<@(kaldi_root)/src/hmm/kaldi-hmm.a',
             '<@(kaldi_root)/src/transform/kaldi-transform.a',
             '<@(kaldi_root)/src/cudamatrix/kaldi-cudamatrix.a',
             '<@(kaldi_root)/src/matrix/kaldi-matrix.a',
             '<@(kaldi_root)/src/fstext/kaldi-fstext.a',
             '<@(kaldi_root)/src/util/kaldi-util.a',
             '<@(kaldi_root)/src/base/kaldi-base.a',
             '<@(kaldi_root)/tools/openfst/lib/libfst.a',
             '<@(kaldi_root)/tools/openfst/lib/libfstngram.a',
             '<@(kaldi_root)/tools/OpenBLAS/libopenblas.a',
          ],
         'library_dirs': [
               '/usr/lib',
          ],
      },
    }
  ]
}
