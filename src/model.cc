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


//
// Possible model layout:
//
// * Default kaldi model with HCLG.fst
//
// * Lookahead model with const G.fst
//
// * Lookahead model with ngram G.fst
//
// * File disambig_tid.int required only for lookadhead models
//
// * File word_boundary.int is required if we want to have precise word timing information
//   otherwise we don't do any word alignment. Optionally lexicon alignment can be done
//   with corresponding C++ code inside kaldi recognizer.

#include "model.h"

#include <sys/stat.h>
#include <fst/fst.h>
#include <fst/register.h>
#include <fst/matcher-fst.h>
#include <fst/extensions/ngram/ngram-fst.h>

namespace fst {

static FstRegisterer<StdOLabelLookAheadFst> OLabelLookAheadFst_StdArc_registerer;
static FstRegisterer<NGramFst<StdArc>> NGramFst_StdArc_registerer;

}  // namespace fst

#ifdef __ANDROID__
#include <android/log.h>
static void AndroidLogHandler(const LogMessageEnvelope &env, const char *message)
{
    __android_log_print(ANDROID_LOG_VERBOSE, "KaldiDemo", message, 1);
}
#endif

Model::Model(const char *model_path) {

#ifdef __ANDROID__
    SetLogHandler(AndroidLogHandler);
#endif

    const char *usage = "Read the docs";
    const char *extra_args[] = {
        "--min-active=200",
        "--max-active=3000",
        "--beam=10.0",
        "--lattice-beam=2.0",
        "--acoustic-scale=1.0",

        "--frame-subsampling-factor=3",

        "--endpoint.silence-phones=1:2:3:4:5:6:7:8:9:10",
        "--endpoint.rule2.min-trailing-silence=0.5",
        "--endpoint.rule3.min-trailing-silence=1.0",
        "--endpoint.rule4.min-trailing-silence=2.0",
    };
    std::string model_path_str(model_path);

    kaldi::ParseOptions po(usage);
    nnet3_decoding_config_.Register(&po);
    endpoint_config_.Register(&po);
    decodable_opts_.Register(&po);

    std::vector<const char*> args;
    args.push_back("vosk");
    args.insert(args.end(), extra_args, extra_args + sizeof(extra_args) / sizeof(extra_args[0]));
    po.Read(args.size(), args.data());

    feature_info_.feature_type = "mfcc";
    ReadConfigFromFile(model_path_str + "/mfcc.conf", &feature_info_.mfcc_opts);

    feature_info_.silence_weighting_config.silence_weight = 1e-3;
    feature_info_.silence_weighting_config.silence_phones_str = "1:2:3:4:5:6:7:8:9:10";

    OnlineIvectorExtractionConfig ivector_extraction_opts;
    ivector_extraction_opts.splice_config_rxfilename = model_path_str + "/ivector/splice.conf";
    ivector_extraction_opts.cmvn_config_rxfilename = model_path_str + "/ivector/online_cmvn.conf";
    ivector_extraction_opts.lda_mat_rxfilename = model_path_str + "/ivector/final.mat";
    ivector_extraction_opts.global_cmvn_stats_rxfilename = model_path_str + "/ivector/global_cmvn.stats";
    ivector_extraction_opts.diag_ubm_rxfilename = model_path_str + "/ivector/final.dubm";
    ivector_extraction_opts.ivector_extractor_rxfilename = model_path_str + "/ivector/final.ie";
    ivector_extraction_opts.num_gselect = 5;
    ivector_extraction_opts.min_post = 0.025;
    ivector_extraction_opts.posterior_scale = 0.1;
    ivector_extraction_opts.max_remembered_frames = 1000;
    ivector_extraction_opts.max_count = 100;
    ivector_extraction_opts.ivector_period = 200;
    feature_info_.use_ivectors = true;
    feature_info_.ivector_extractor_info.Init(ivector_extraction_opts);

    nnet3_rxfilename_ = model_path_str + "/final.mdl";
    hclg_fst_rxfilename_ = model_path_str + "/HCLG.fst";
    hcl_fst_rxfilename_ = model_path_str + "/HCLr.fst";
    g_fst_rxfilename_ = model_path_str + "/Gr.fst";
    disambig_rxfilename_ = model_path_str + "/disambig_tid.int";
    word_syms_rxfilename_ = model_path_str + "/words.txt";
    winfo_rxfilename_ = model_path_str + "/word_boundary.int";

    trans_model_ = new kaldi::TransitionModel();
    nnet_ = new kaldi::nnet3::AmNnetSimple();
    {
        bool binary;
        kaldi::Input ki(nnet3_rxfilename_, &binary);
        trans_model_->Read(ki.Stream(), binary);
        nnet_->Read(ki.Stream(), binary);
        SetBatchnormTestMode(true, &(nnet_->GetNnet()));
        SetDropoutTestMode(true, &(nnet_->GetNnet()));
        nnet3::CollapseModel(nnet3::CollapseModelConfig(), &(nnet_->GetNnet()));
    }

    decodable_info_ = new nnet3::DecodableNnetSimpleLoopedInfo(decodable_opts_,
                                                               nnet_);
    struct stat buffer;
    if (stat(hclg_fst_rxfilename_.c_str(), &buffer) == 0) {
        hclg_fst_ = fst::ReadFstKaldiGeneric(hclg_fst_rxfilename_);
        hcl_fst_ = NULL;
        g_fst_ = NULL;
    } else {
        hclg_fst_ = NULL;
        hcl_fst_ = fst::StdFst::Read(hcl_fst_rxfilename_);
        g_fst_ = fst::StdFst::Read(g_fst_rxfilename_);

        ReadIntegerVectorSimple(disambig_rxfilename_, &disambig_);
    }

    word_syms_ = NULL;
    if (hclg_fst_ && hclg_fst_->OutputSymbols()) {
        word_syms_ = hclg_fst_->OutputSymbols();
    } else if (g_fst_ && g_fst_->OutputSymbols()) {
        word_syms_ = g_fst_->OutputSymbols();
    }
    if (!word_syms_) {
        if (!(word_syms_ = fst::SymbolTable::ReadText(word_syms_rxfilename_)))
            KALDI_ERR << "Could not read symbol table from file "
                      << word_syms_rxfilename_;
    }
    KALDI_ASSERT(word_syms_);

    if (stat(winfo_rxfilename_.c_str(), &buffer) == 0) {
        kaldi::WordBoundaryInfoNewOpts opts;
        winfo_ = new kaldi::WordBoundaryInfo(opts, winfo_rxfilename_);
    } else {
        winfo_ = NULL;
    }
}

Model::~Model() {
    delete decodable_info_;
    delete trans_model_;
    delete nnet_;
    delete winfo_;
    delete hclg_fst_;
    delete hcl_fst_;
    delete g_fst_;
}

float Model::GetSampleFrequency() const {
    return feature_info_.mfcc_opts.frame_opts.samp_freq;
}

void Model::SetAllowDownsample(bool val) {
    feature_info_.mfcc_opts.frame_opts.allow_downsample = val;
}

void Model::SetAllowUpsample(bool val) {
    feature_info_.mfcc_opts.frame_opts.allow_upsample = val;
}
