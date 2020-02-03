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

#ifndef model_H_
#define model_H_

#include "base/kaldi-common.h"
#include "fstext/fstext-lib.h"
#include "fstext/fstext-utils.h"
#include "online2/onlinebin-util.h"
#include "online2/online-timing.h"
#include "online2/online-endpoint.h"
#include "online2/online-nnet3-decoding.h"
#include "online2/online-feature-pipeline.h"
#include "lat/lattice-functions.h"
#include "lat/sausages.h"
#include "lat/word-align-lattice.h"
#include "lm/const-arpa-lm.h"
#include "util/parse-options.h"
#include "nnet3/nnet-utils.h"
#include "rnnlm/rnnlm-utils.h"

using namespace kaldi;

class KaldiRecognizer;

class Model {

public:
    Model(const char *model_path);
    ~Model();
    int SampleFrequency() const;
    void SetAllowDownsample(bool val);
    void SetAllowUpsample(bool val);

protected:
    friend class KaldiRecognizer;

    std::string nnet3_rxfilename_;
    std::string hclg_fst_rxfilename_;
    std::string hcl_fst_rxfilename_;
    std::string g_fst_rxfilename_;
    std::string word_syms_rxfilename_;
    std::string winfo_rxfilename_;
    std::string disambig_rxfilename_;

    kaldi::OnlineEndpointConfig endpoint_config_;
    kaldi::LatticeFasterDecoderConfig nnet3_decoding_config_;
    kaldi::nnet3::NnetSimpleLoopedComputationOptions decodable_opts_;
    kaldi::OnlineNnet2FeaturePipelineInfo feature_info_;

    kaldi::nnet3::DecodableNnetSimpleLoopedInfo *decodable_info_;
    kaldi::TransitionModel *trans_model_;
    kaldi::nnet3::AmNnetSimple *nnet_;
    const fst::SymbolTable *word_syms_;
    kaldi::WordBoundaryInfo *winfo_;
    std::vector<int32> disambig_;

    fst::Fst<fst::StdArc> *hclg_fst_;
    fst::Fst<fst::StdArc> *hcl_fst_;
    fst::Fst<fst::StdArc> *g_fst_;
};

#endif /* model_H_ */
