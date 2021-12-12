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

#include "batch_recognizer.h"

#include "fstext/fstext-utils.h"
#include "lat/sausages.h"

using namespace fst;
using namespace kaldi::nnet3;
using CorrelationID = CudaOnlinePipelineDynamicBatcher::CorrelationID;

BatchRecognizer::BatchRecognizer(Model *model, float sample_frequency) : model_(model), sample_frequency_(sample_frequency) {
    model_->Ref();

    BatchedThreadedNnet3CudaOnlinePipelineConfig batched_decoder_config;

    cuda_pipeline_ = new BatchedThreadedNnet3CudaOnlinePipeline 
         (batched_decoder_config, *model_->hclg_fst_, *model_->nnet_, *model_->trans_model_);

    CudaOnlinePipelineDynamicBatcherConfig dynamic_batcher_config;
    dynamic_batcher_ = new CudaOnlinePipelineDynamicBatcher(dynamic_batcher_config,
                                                            *cuda_pipeline_);

    InitRescoring();
}

BatchRecognizer::~BatchRecognizer() {
    delete lm_to_subtract_;
    delete carpa_to_add_;
    delete carpa_to_add_scale_;

    delete cuda_pipeline_;
    delete dynamic_batcher_;

    model_->Unref();
}

void BatchRecognizer::InitRescoring()
{
    if (model_->graph_lm_fst_) {
        fst::CacheOptions cache_opts(true, -1);
        fst::ArcMapFstOptions mapfst_opts(cache_opts);
        fst::StdToLatticeMapper<BaseFloat> mapper;
        lm_to_subtract_ = new fst::ArcMapFst<fst::StdArc, LatticeArc, fst::StdToLatticeMapper<BaseFloat> >(*model_->graph_lm_fst_, mapper, mapfst_opts);
        carpa_to_add_ = new ConstArpaLmDeterministicFst(model_->const_arpa_);
    }
}

void BatchRecognizer::FinishStream(uint64_t id)
{
    streams_.erase(id);
}

void BatchRecognizer::AcceptWaveform(uint64_t id, const char *data, int len)
{
    bool first = false;

    if (streams_.find(id) == streams_.end()) {
        first = true;
        streams_.insert(id);

        // Define the callback for results.
        cuda_pipeline_->SetBestPathCallback(
          id,
          [&, id](const std::string &str, bool partial,
                       bool endpoint_detected) {
              if (partial) {
                  KALDI_LOG << "id #" << id << " [partial] : " << str;
              }

              if (endpoint_detected) {
                  KALDI_LOG << "id #" << id << " [endpoint detected]";
              }

              if (!partial) {
                  KALDI_LOG << "id #" << id << " : " << str;
              }
            });
    }

    Vector<BaseFloat> wave;
    wave.Resize(len / 2, kUndefined);
    for (int i = 0; i < len / 2; i++)
        wave(i) = *(((short *)data) + i);
    SubVector<BaseFloat> chunk(wave.Data(), 0);

    dynamic_batcher_->Push(id, first, false, chunk);
}

const char* BatchRecognizer::PullResults()
{
    dynamic_batcher_->WaitForCompletion();
    cudaDeviceSynchronize();
    return "";
}
