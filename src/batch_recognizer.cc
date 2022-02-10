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
#include "json.h"

#include <sys/stat.h>

using namespace fst;
using namespace kaldi::nnet3;
using CorrelationID = CudaOnlinePipelineDynamicBatcher::CorrelationID;

BatchRecognizer::BatchRecognizer() {
    BatchedThreadedNnet3CudaOnlinePipelineConfig batched_decoder_config;

    kaldi::ParseOptions po("something");
    batched_decoder_config.Register(&po);
    po.ReadConfigFile("model/conf/model.conf");

    struct stat buffer;

    string nnet3_rxfilename_ = "model/am/final.mdl";
    string hclg_fst_rxfilename_ = "model/graph/HCLG.fst";
    string word_syms_rxfilename_ = "model/graph/words.txt";
    string winfo_rxfilename_ = "model/graph/phones/word_boundary.int";
    string std_fst_rxfilename_ = "model/rescore/G.fst";
    string carpa_rxfilename_ = "model/rescore/G.carpa";

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

    if (stat(carpa_rxfilename_.c_str(), &buffer) == 0) {
        KALDI_LOG << "Loading subtract G.fst model from " << std_fst_rxfilename_;
        graph_lm_fst_ = fst::ReadAndPrepareLmFst(std_fst_rxfilename_);
        KALDI_LOG << "Loading CARPA model from " << carpa_rxfilename_;
        ReadKaldiObject(carpa_rxfilename_, &const_arpa_);
    }

    batched_decoder_config.num_worker_threads = -1;
    batched_decoder_config.max_batch_size = 32;
    batched_decoder_config.num_channels = 600;
    batched_decoder_config.reset_on_endpoint = true;
    batched_decoder_config.use_gpu_feature_extraction = true;

    batched_decoder_config.feature_opts.feature_type = "mfcc";
    batched_decoder_config.feature_opts.mfcc_config = "model/conf/mfcc.conf";
    batched_decoder_config.feature_opts.ivector_extraction_config = "model/conf/ivector.conf";
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
         (batched_decoder_config, *hclg_fst_, *nnet_, *trans_model_);
    cuda_pipeline_->SetSymbolTable(*word_syms_);

    CudaOnlinePipelineDynamicBatcherConfig dynamic_batcher_config;
    dynamic_batcher_ = new CudaOnlinePipelineDynamicBatcher(dynamic_batcher_config,
                                                            *cuda_pipeline_);

    samples_per_chunk_ = cuda_pipeline_->GetNSampsPerChunk();
}

BatchRecognizer::~BatchRecognizer() {

    delete trans_model_;
    delete nnet_;
    delete word_syms_;
    delete winfo_;
    delete hclg_fst_;
    delete graph_lm_fst_;

    delete lm_to_subtract_;
    delete carpa_to_add_;
    delete carpa_to_add_scale_;

    delete cuda_pipeline_;
    delete dynamic_batcher_;
}

void BatchRecognizer::FinishStream(uint64_t id)
{
    auto it = streams_.find(id);
    if (it == streams_.end()) {
        return;
    }

    SubVector<BaseFloat> chunk = it->second.buffer.Range(0, it->second.buffer.Dim());
    dynamic_batcher_->Push(id, !(it->second.initialized), true, chunk);
    streams_.erase(it);
}

void BatchRecognizer::PushLattice(uint64_t id, CompactLattice &clat, BaseFloat offset)
{
    fst::ScaleLattice(fst::GraphLatticeScale(0.9), &clat);

    CompactLattice aligned_lat;
    WordAlignLattice(clat, *trans_model_, *winfo_, 0, &aligned_lat);

    MinimumBayesRisk mbr(aligned_lat);
    const vector<BaseFloat> &conf = mbr.GetOneBestConfidences();
    const vector<int32> &words = mbr.GetOneBest();
    const vector<pair<BaseFloat, BaseFloat> > &times =
          mbr.GetOneBestTimes();

    int size = words.size();

    json::JSON obj;
    stringstream text;

    // Create JSON object
    for (int i = 0; i < size; i++) {
        json::JSON word;

        word["word"] = word_syms_->Find(words[i]);
        word["start"] = round(times[i].first) * 0.03 + offset;
        word["end"] = round(times[i].second) * 0.03 + offset;
        word["conf"] = conf[i];
        obj["result"].append(word);

        if (i) {
            text << " ";
        }
        text << word_syms_->Find(words[i]);
    }
    obj["text"] = text.str();

//    KALDI_LOG << "Result " << id << " " << obj.dump();

    streams_[id].results.push(obj.dump());
}

void BatchRecognizer::AcceptWaveform(uint64_t id, const char *data, int len)
{
    if (streams_.find(id) == streams_.end()) {
        // Define the callback for results.
#if 0
         cuda_pipeline_->SetBestPathCallback(
          id,
          [&, id](const std::string &str, bool partial,
                       bool endpoint_detected) {
              if (partial) {
                  KALDI_LOG << "id #" << id << " [partial] : " << str << ":";
              }

              if (endpoint_detected) {
                  KALDI_LOG << "id #" << id << " [endpoint detected]";
              }

              if (!partial) {
                  KALDI_LOG << "id #" << id << " : " << str;
              }
            });
#endif
        cuda_pipeline_->SetLatticeCallback(
          id,
          [&, id](SegmentedLatticeCallbackParams& params) {
              if (params.results.empty()) {
                  KALDI_WARN << "Empty result for callback";
                  return;
              }
              CompactLattice *clat = params.results[0].GetLatticeResult();
              BaseFloat offset = params.results[0].GetTimeOffsetSeconds();
              PushLattice(id, *clat, offset);
          },
          CudaPipelineResult::RESULT_TYPE_LATTICE);
    }
    // Collect data so we process exactly samples_per_chunk_
    Vector<BaseFloat> &buffer = streams_[id].buffer;
    int32 end = buffer.Dim();
    buffer.Resize(end + len / 2, kCopyData);
    for (int i = 0; i < len / 2; i++)
        buffer(i + end) = *(((short *)data) + i);
    end = buffer.Dim();

    // Pick chunks and submit them to the batcher
    int32 i = 0;
    while (i + samples_per_chunk_ <= end) {
        dynamic_batcher_->Push(id, (!streams_[id].initialized), false,
                                    buffer.Range(i, samples_per_chunk_));
        streams_[id].initialized = true;
        i += samples_per_chunk_;
    }

    // Keep remaining data
    if (i > 0) {
        int32 tail = end - i;
        for (int j = 0; j < tail; j++) {
            buffer(j) = buffer(i + j);
        }
        buffer.Resize(tail, kCopyData);
    }
}

const char* BatchRecognizer::FrontResult(uint64_t id)
{
    auto it = streams_.find(id);
    if (it == streams_.end()) {
        return "";
    }
    if (it->second.results.empty()) {
        return "";
    }
    return it->second.results.front().c_str();
}

void BatchRecognizer::Pop(uint64_t id)
{
    auto it = streams_.find(id);
    if (it == streams_.end()) {
        return;
    }
    if (it->second.results.empty()) {
        return;
    }
    it->second.results.pop();
}

void BatchRecognizer::WaitForCompletion()
{
    dynamic_batcher_->WaitForCompletion();
}

int BatchRecognizer::GetNumPendingChunks(uint64_t id)
{
    return dynamic_batcher_->GetNumPendingChunks(id);
}
