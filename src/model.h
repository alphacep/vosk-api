// Copyright 2019-2021 Alpha Cephei Inc.
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

#ifndef VOSK_MODEL_H
#define VOSK_MODEL_H

#include "base/kaldi-common.h"
#include "fstext/fstext-lib.h"
#include "fstext/fstext-utils.h"
#include "online2/onlinebin-util.h"
#include "online2/online-timing.h"
#include "online2/online-endpoint.h"
#include "online2/online-nnet3-incremental-decoding.h"
#include "online2/online-feature-pipeline.h"
#include "lat/lattice-functions.h"
#include "lat/sausages.h"
#include "lat/word-align-lattice.h"
#include "lm/const-arpa-lm.h"
#include "util/parse-options.h"
#include "nnet3/nnet-utils.h"
#include "rnnlm/rnnlm-utils.h"
#include "rnnlm/rnnlm-lattice-rescoring.h"
#include <atomic>

using namespace kaldi;
using namespace std;

class Recognizer;

class Model {

public:
    Model(const char *model_path);
    void Ref();
    void Unref();
    int FindWord(const char *word);

protected:
    ~Model();
    void ConfigureV1();
    void ConfigureV2();
    void ReadDataFiles();

    friend class Recognizer;

    string model_path_str_;
    string nnet3_rxfilename_;
    string hclg_fst_rxfilename_;
    string hcl_fst_rxfilename_;
    string g_fst_rxfilename_;
    string disambig_rxfilename_;
    string word_syms_rxfilename_;
    string winfo_rxfilename_;
    string carpa_rxfilename_;
    string std_fst_rxfilename_;
    string final_ie_rxfilename_;
    string mfcc_conf_rxfilename_;
    string fbank_conf_rxfilename_;
    string global_cmvn_stats_rxfilename_;
    string pitch_conf_rxfilename_;
    string phone_syms_rxfilename_;

    string rnnlm_word_feats_rxfilename_;
    string rnnlm_feat_embedding_rxfilename_;
    string rnnlm_config_rxfilename_;
    string rnnlm_lm_rxfilename_;

    kaldi::OnlineEndpointConfig endpoint_config_;
    kaldi::LatticeIncrementalDecoderConfig nnet3_decoding_config_;
    kaldi::nnet3::NnetSimpleLoopedComputationOptions decodable_opts_;
    kaldi::OnlineNnet2FeaturePipelineInfo feature_info_;

    kaldi::nnet3::DecodableNnetSimpleLoopedInfo *decodable_info_ = nullptr;
    kaldi::TransitionModel *trans_model_ = nullptr;
    kaldi::nnet3::AmNnetSimple *nnet_ = nullptr;
    const fst::SymbolTable *word_syms_ = nullptr;
    bool word_syms_loaded_ = false;
    kaldi::WordBoundaryInfo *winfo_ = nullptr;
    vector<int32> disambig_;
    const fst::SymbolTable *phone_symbol_table_;
    bool phone_syms_loaded_;

    fst::Fst<fst::StdArc> *hclg_fst_ = nullptr;
    fst::Fst<fst::StdArc> *hcl_fst_ = nullptr;
    fst::Fst<fst::StdArc> *g_fst_ = nullptr;

    fst::VectorFst<fst::StdArc> *graph_lm_fst_ = nullptr;
    kaldi::ConstArpaLm const_arpa_;

    kaldi::rnnlm::RnnlmComputeStateComputationOptions rnnlm_compute_opts;
    CuMatrix<BaseFloat> word_embedding_mat;
    kaldi::nnet3::Nnet rnnlm;
    bool rnnlm_enabled_ = false;

    std::atomic<int> ref_cnt_;
};

#endif /* VOSK_MODEL_H */
