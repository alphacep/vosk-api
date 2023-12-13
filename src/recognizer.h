// Copyright 2019 Alpha Cephei Inc.
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//       http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License.

#ifndef VOSK_KALDI_RECOGNIZER_H
#define VOSK_KALDI_RECOGNIZER_H

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "fstext/fstext-lib.h"
#include "fstext/fstext-utils.h"
#include "decoder/lattice-faster-decoder.h"
#include "feat/feature-mfcc.h"
#include "lat/kaldi-lattice.h"
#include "lat/word-align-lattice.h"
#include "lat/compose-lattice-pruned.h"
#include "nnet3/am-nnet-simple.h"
#include "nnet3/nnet-am-decodable-simple.h"
#include "nnet3/nnet-utils.h"

#include "model.h"
#include "spk_model.h"

using namespace kaldi;

enum RecognizerState {
    RECOGNIZER_INITIALIZED,
    RECOGNIZER_RUNNING,
    RECOGNIZER_ENDPOINT,
    RECOGNIZER_FINALIZED
};

class Recognizer {
    public:
        Recognizer(Model *model, float sample_frequency);
        Recognizer(Model *model, float sample_frequency, SpkModel *spk_model);
        Recognizer(Model *model, float sample_frequency, char const *grammar);
        ~Recognizer();
        void SetMaxAlternatives(int max_alternatives);
        void SetSpkModel(SpkModel *spk_model);
        void SetGrm(char const *grammar);
        void SetWords(bool words);
        void SetPartialWords(bool partial_words);
        void SetNLSML(bool nlsml);
        void SetEndpointerMode(int mode);
        void SetEndpointerDelays(float t_start_max, float t_end, float t_max);
        bool AcceptWaveform(const char *data, int len);
        bool AcceptWaveform(const short *sdata, int len);
        bool AcceptWaveform(const float *fdata, int len);
        const char* Result();
        const char* FinalResult();
        const char* PartialResult();
        void Reset();

    private:
        void InitState();
        void InitRescoring();
        void CleanUp();
        void UpdateSilenceWeights();
        void UpdateGrammarFst(char const *grammar);
        bool AcceptWaveform(Vector<BaseFloat> &wdata);
        bool GetSpkVector(Vector<BaseFloat> &out_xvector, int *frames);
        const char *GetResult();
        const char *StoreEmptyReturn();
        const char *StoreReturn(const string &res);
        const char *MbrResult(CompactLattice &clat);
        const char *NbestResult(CompactLattice &clat);
        const char *NlsmlResult(CompactLattice &clat);

        Model *model_ = nullptr;
        SingleUtteranceNnet3IncrementalDecoder *decoder_ = nullptr;
        fst::LookaheadFst<fst::StdArc, int32> *decode_fst_ = nullptr;
        fst::StdVectorFst *g_fst_ = nullptr; // dynamically constructed grammar
        OnlineNnet2FeaturePipeline *feature_pipeline_ = nullptr;
        OnlineSilenceWeighting *silence_weighting_ = nullptr;
        // Endpointer
        kaldi::OnlineEndpointConfig endpoint_config_;

        // Speaker identification
        SpkModel *spk_model_ = nullptr;
        OnlineBaseFeature *spk_feature_ = nullptr;

        // Rescoring
        fst::ArcMapFst<fst::StdArc, LatticeArc, fst::StdToLatticeMapper<BaseFloat> > *lm_to_subtract_ = nullptr;
        kaldi::ConstArpaLmDeterministicFst *carpa_to_add_ = nullptr;
        fst::ScaleDeterministicOnDemandFst *carpa_to_add_scale_ = nullptr;
        // RNNLM rescoring
        kaldi::rnnlm::KaldiRnnlmDeterministicFst* rnnlm_to_add_ = nullptr;
        fst::DeterministicOnDemandFst<fst::StdArc> *rnnlm_to_add_scale_ = nullptr;
        kaldi::rnnlm::RnnlmComputeStateInfo *rnnlm_info_ = nullptr;


        // Other
        int max_alternatives_ = 0; // Disable alternatives by default
        bool words_ = false;
        bool partial_words_ = false;
        bool nlsml_ = false;

        float sample_frequency_;
        int32 frame_offset_;

        int64 samples_processed_;
        int64 samples_round_start_;

        RecognizerState state_;
        string last_result_;
};

#endif /* VOSK_KALDI_RECOGNIZER_H */
