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

#include "kaldi_recognizer.h"

#include "fstext/fstext-utils.h"
#include "lat/sausages.h"

using namespace fst;
using namespace kaldi::nnet3;

KaldiRecognizer::KaldiRecognizer(Model &model, float sample_frequency) : model_(model), sample_frequency_(sample_frequency) {

    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_.feature_info_);
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_.trans_model_, model_.feature_info_.silence_weighting_config, 3);

    if (!model_.hclg_fst_) {
        if (model_.hcl_fst_ && model_.g_fst_) {
            decode_fst_ = LookaheadComposeFst(*model_.hcl_fst_, *model_.g_fst_, model_.disambig_);
        } else {
            KALDI_ERR << "Can't create decoding graph";
        }
    } else {
        decode_fst_ = NULL;
    }

    decoder_ = new kaldi::SingleUtteranceNnet3Decoder(model_.nnet3_decoding_config_,
            *model_.trans_model_,
            *model_.decodable_info_,
            model_.hclg_fst_ ? *model.hclg_fst_ : *decode_fst_,
            feature_pipeline_);

    frame_offset_ = 0;
    input_finalized_ = false;
}

KaldiRecognizer::~KaldiRecognizer() {
    delete feature_pipeline_;
    delete silence_weighting_;
    delete decoder_;
    delete decode_fst_;
}

void KaldiRecognizer::CleanUp()
{
    delete silence_weighting_;
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_.trans_model_, model_.feature_info_.silence_weighting_config, 3);

    frame_offset_ += decoder_->NumFramesDecoded();
    decoder_->InitDecoding(frame_offset_);
}

void KaldiRecognizer::UpdateSilenceWeights()
{
    if (silence_weighting_->Active() && feature_pipeline_->NumFramesReady() > 0 &&
        feature_pipeline_->IvectorFeature() != NULL) {
        std::vector<std::pair<int32, BaseFloat> > delta_weights;
        silence_weighting_->ComputeCurrentTraceback(decoder_->Decoder());
        silence_weighting_->GetDeltaWeights(feature_pipeline_->NumFramesReady(),
                                          frame_offset_ * 3,
                                          &delta_weights);
        feature_pipeline_->UpdateFrameWeights(delta_weights);
    }
}

bool KaldiRecognizer::AcceptWaveform(const char *data, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len / 2, kUndefined);
    for (int i = 0; i < len / 2; i++)
        wave(i) = *(((short *)data) + i);
    return AcceptWaveform(wave);
}

bool KaldiRecognizer::AcceptWaveform(const short *sdata, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len, kUndefined);
    for (int i = 0; i < len; i++)
        wave(i) = sdata[i];
    return AcceptWaveform(wave);
}

bool KaldiRecognizer::AcceptWaveform(const float *fdata, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len, kUndefined);
    for (int i = 0; i < len; i++)
        wave(i) = fdata[i];
    return AcceptWaveform(wave);
}

bool KaldiRecognizer::AcceptWaveform(Vector<BaseFloat> &wdata)
{
    if (input_finalized_) {
        CleanUp();
        input_finalized_ = false;
    }

    feature_pipeline_->AcceptWaveform(sample_frequency_, wdata);
    UpdateSilenceWeights();
    decoder_->AdvanceDecoding();

    if (decoder_->EndpointDetected(model_.endpoint_config_)) {
        return true;
    }

    return false;
}

std::string KaldiRecognizer::Result()
{

    if (!input_finalized_) {
        decoder_->FinalizeDecoding();
        input_finalized_ = true;
    }

    kaldi::CompactLattice clat;
    decoder_->GetLattice(true, &clat);
    fst::ScaleLattice(fst::LatticeScale(8.0, 10.0), &clat);

    CompactLattice aligned_lat;
    if (model_.winfo_) {
        WordAlignLattice(clat, *model_.trans_model_, *model_.winfo_, 0, &aligned_lat);
    } else {
        aligned_lat = clat;
    }

    MinimumBayesRisk mbr(aligned_lat);
    const std::vector<BaseFloat> &conf = mbr.GetOneBestConfidences();
    const std::vector<int32> &words = mbr.GetOneBest();
    const std::vector<std::pair<BaseFloat, BaseFloat> > &times =
          mbr.GetOneBestTimes();

    int size = words.size();

    std::stringstream ss;

    // Create JSON object
    ss << "{\"result\" : [ ";
    for (int i = 0; i < size; i++) {
        ss << "{\"word\": \"" << model_.word_syms_->Find(words[i]) << "\", \"start\" : " << (frame_offset_ + times[i].first) * 0.03 << "," <<
                " \"end\" : " << (frame_offset_ + times[i].second) * 0.03 << ", \"conf\" : " << conf[i] << "}";
        if (i != size - 1)
            ss << ",\n";
        else
            ss << "\n";
    }
    ss << " ], \"text\" : \"";
    for (int i = 0; i < size; i++) {
        ss << model_.word_syms_->Find(words[i]);
        if (i != size - 1)
            ss << " ";
    }
    ss << "\" }";

    return ss.str();
}

std::string KaldiRecognizer::PartialResult()
{
    if (decoder_->NumFramesDecoded() == 0) {
        return "{\"partial\" : \"\"}";
    }

    kaldi::Lattice lat;
    decoder_->GetBestPath(false, &lat);
    std::vector<kaldi::int32> alignment, words;
    LatticeWeight weight;
    GetLinearSymbolSequence(lat, &alignment, &words, &weight);

    std::ostringstream outss;
    outss << "{\"partial\" : \"";
    for (size_t i = 0; i < words.size(); i++) {
        if (i) {
            outss << " ";
        }
        outss << model_.word_syms_->Find(words[i]);
    }
    outss << "\"}";

    return outss.str();
}

std::string KaldiRecognizer::FinalResult()
{
    if (!input_finalized_) {
        feature_pipeline_->InputFinished();
        UpdateSilenceWeights();
        decoder_->AdvanceDecoding();
        decoder_->FinalizeDecoding();
        input_finalized_ = true;
    }
    return Result();
}
