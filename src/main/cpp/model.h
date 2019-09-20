// model.h

// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//
//  http://www.apache.org/licenses/LICENSE-2.0
//
// THIS CODE IS PROVIDED *AS IS* BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
// KIND, EITHER EXPRESS OR IMPLIED, INCLUDING WITHOUT LIMITATION ANY IMPLIED
// WARRANTIES OR CONDITIONS OF TITLE, FITNESS FOR A PARTICULAR PURPOSE,
// MERCHANTABLITY OR NON-INFRINGEMENT.
// See the Apache 2 License for the specific language governing permissions and
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

protected:
    friend class KaldiRecognizer;

    std::string nnet3_rxfilename_;
    std::string hcl_fst_rxfilename_;
    std::string g_fst_rxfilename_;
    std::string word_syms_rxfilename_;

    kaldi::OnlineEndpointConfig endpoint_config_;
    kaldi::LatticeFasterDecoderConfig nnet3_decoding_config_;
    kaldi::nnet3::NnetSimpleLoopedComputationOptions decodable_opts_;

    kaldi::OnlineNnet2FeaturePipelineInfo feature_info_;
    kaldi::BaseFloat sample_frequency;

    kaldi::nnet3::DecodableNnetSimpleLoopedInfo *decodable_info_;
    kaldi::TransitionModel *trans_model_;
    kaldi::nnet3::AmNnetSimple *nnet_;
    fst::SymbolTable *word_syms_;
    kaldi::WordBoundaryInfo *winfo_;

    fst::Fst<fst::StdArc> *hcl_fst_;
    fst::Fst<fst::StdArc> *g_fst_;
};

#endif /* model_H_ */
