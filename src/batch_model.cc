// Copyright 2019-2020 Alpha Cephei Inc.
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

#include "batch_model.h"

#include <sys/stat.h>

using namespace fst;
using namespace kaldi::nnet3;
using CorrelationID = CudaOnlinePipelineDynamicBatcher::CorrelationID;

BatchModel::BatchModel(const char *model_path) : model_path_str_(model_path) {
    BatchedThreadedNnet3CudaOnlinePipelineConfig batched_decoder_config;

    kaldi::ParseOptions po("something");
    batched_decoder_config.Register(&po);
    po.ReadConfigFile(model_path_str_ + "/conf/model.conf");

    struct stat buffer;

    string nnet3_rxfilename_ = model_path_str_ + "/am/final.mdl";
    string hclg_fst_rxfilename_ = model_path_str_ + "/graph/HCLG.fst";
    string word_syms_rxfilename_ = model_path_str_ + "/graph/words.txt";
    string winfo_rxfilename_ = model_path_str_ + "/graph/phones/word_boundary.int";
    string std_fst_rxfilename_ = model_path_str_ + "/rescore/G.fst";
    string carpa_rxfilename_ = model_path_str_ + "/rescore/G.carpa";

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

    if (stat(hclg_fst_rxfilename_.c_str(), &buffer) == 0) {
        KALDI_LOG << "Loading HCLG from " << hclg_fst_rxfilename_;
        hclg_fst_ = fst::ReadFstKaldiGeneric(hclg_fst_rxfilename_);
    }

    KALDI_LOG << "Loading words from " << word_syms_rxfilename_;
    if (!(word_syms_ = fst::SymbolTable::ReadText(word_syms_rxfilename_))) {
        KALDI_ERR << "Could not read symbol table from file "
                  << word_syms_rxfilename_;
    }
    KALDI_ASSERT(word_syms_);

    if (stat(winfo_rxfilename_.c_str(), &buffer) == 0) {
        KALDI_LOG << "Loading winfo " << winfo_rxfilename_;
        kaldi::WordBoundaryInfoNewOpts opts;
        winfo_ = new kaldi::WordBoundaryInfo(opts, winfo_rxfilename_);
    }

    batched_decoder_config.num_worker_threads = -1;
    batched_decoder_config.max_batch_size = 32;
    batched_decoder_config.num_channels = 600;
    batched_decoder_config.reset_on_endpoint = true;
    batched_decoder_config.use_gpu_feature_extraction = true;

    feature_info_.feature_type = "mfcc";
    ReadConfigFromFile(model_path_str_ + "/conf/mfcc.conf", &feature_info_.mfcc_opts);
    feature_info_.silence_weighting_config.silence_weight = 1e-3;
    feature_info_.silence_weighting_config.silence_phones_str = batched_decoder_config.decoder_opts.endpointing_config.silence_phones;

    OnlineIvectorExtractionConfig ivector_extraction_opts;
    ivector_extraction_opts.splice_config_rxfilename = model_path_str_ + "/ivector/splice.conf";
    ivector_extraction_opts.cmvn_config_rxfilename = model_path_str_ + "/ivector/online_cmvn.conf";
    ivector_extraction_opts.lda_mat_rxfilename = model_path_str_ + "/ivector/final.mat";
    ivector_extraction_opts.global_cmvn_stats_rxfilename = model_path_str_ + "/ivector/global_cmvn.stats";
    ivector_extraction_opts.diag_ubm_rxfilename = model_path_str_ + "/ivector/final.dubm";
    ivector_extraction_opts.ivector_extractor_rxfilename = model_path_str_ + "/ivector/final.ie";
    ivector_extraction_opts.max_count = 100;
    feature_info_.use_ivectors = true;
    feature_info_.ivector_extractor_info.Init(ivector_extraction_opts);


    batched_decoder_config.decoder_opts.max_active = 7000;
    batched_decoder_config.decoder_opts.default_beam = 13.0;
    batched_decoder_config.decoder_opts.lattice_beam = 6.0;
    batched_decoder_config.compute_opts.acoustic_scale = 1.0;
    batched_decoder_config.compute_opts.frame_subsampling_factor = 3;

    int32 nnet_left_context, nnet_right_context;
    nnet3::ComputeSimpleNnetContext(nnet_->GetNnet(), &nnet_left_context,
                                    &nnet_right_context);

    batched_decoder_config.compute_opts.frames_per_chunk = std::max(51, (nnet_right_context + 3 - nnet_right_context % 3));

    cuda_pipeline_ = new BatchedThreadedNnet3CudaOnlinePipeline 
         (batched_decoder_config, feature_info_, *hclg_fst_, *nnet_, *trans_model_);
    cuda_pipeline_->SetSymbolTable(*word_syms_);

    CudaOnlinePipelineDynamicBatcherConfig dynamic_batcher_config;
    dynamic_batcher_ = new CudaOnlinePipelineDynamicBatcher(dynamic_batcher_config,
                                                            *cuda_pipeline_);

    samples_per_chunk_ = cuda_pipeline_->GetNSampsPerChunk();
    last_id_ = 0;
}

uint64_t BatchModel::GetID(BatchRecognizer *recognizer) {
    return last_id_++;
}

BatchModel::~BatchModel() {

    delete trans_model_;
    delete nnet_;
    delete word_syms_;
    delete winfo_;
    delete hclg_fst_;

    delete cuda_pipeline_;
    delete dynamic_batcher_;
}

void BatchModel::WaitForCompletion()
{
    dynamic_batcher_->WaitForCompletion();
}
