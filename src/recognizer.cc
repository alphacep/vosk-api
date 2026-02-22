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

#include "recognizer.h"
#include "json.h"
#include "fstext/fstext-utils.h"
#include "lat/sausages.h"
#include "language_model.h"

using namespace fst;
using namespace kaldi::nnet3;

Recognizer::Recognizer(Model *model, float sample_frequency) : model_(model), spk_model_(0), sample_frequency_(sample_frequency) {

    model_->Ref();

    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_->feature_info_);
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

    if (!model_->hclg_fst_) {
        if (model_->hcl_fst_ && model_->g_fst_) {
            decode_fst_ = LookaheadComposeFst(*model_->hcl_fst_, *model_->g_fst_, model_->disambig_);
        } else {
            KALDI_ERR << "Can't create decoding graph";
        }
    }

    decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(model_->nnet3_decoding_config_,
            *model_->trans_model_,
            *model_->decodable_info_,
            model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_,
            feature_pipeline_);

    InitState();
    InitRescoring();
}

Recognizer::Recognizer(Model *model, float sample_frequency, char const *grammar) : model_(model), spk_model_(0), sample_frequency_(sample_frequency)
{
    model_->Ref();

    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_->feature_info_);
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

    if (model_->hcl_fst_) {
        UpdateGrammarFst(grammar);
    } else {
        KALDI_WARN << "Runtime graphs are not supported by this model";
    }

    decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(model_->nnet3_decoding_config_,
            *model_->trans_model_,
            *model_->decodable_info_,
            model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_,
            feature_pipeline_);

    InitState();
    InitRescoring();
}

Recognizer::Recognizer(Model *model, float sample_frequency, SpkModel *spk_model) : model_(model), spk_model_(spk_model), sample_frequency_(sample_frequency) {

    model_->Ref();
    spk_model->Ref();

    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_->feature_info_);
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

    if (!model_->hclg_fst_) {
        if (model_->hcl_fst_ && model_->g_fst_) {
            decode_fst_ = LookaheadComposeFst(*model_->hcl_fst_, *model_->g_fst_, model_->disambig_);
        } else {
            KALDI_ERR << "Can't create decoding graph";
        }
    }

    decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(model_->nnet3_decoding_config_,
            *model_->trans_model_,
            *model_->decodable_info_,
            model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_,
            feature_pipeline_);

    spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);

    InitState();
    InitRescoring();
}

Recognizer::~Recognizer() {
    delete decoder_;
    delete feature_pipeline_;
    delete silence_weighting_;
    delete g_fst_;
    delete decode_fst_;
    delete spk_feature_;

    delete lm_to_subtract_;
    delete carpa_to_add_;
    delete carpa_to_add_scale_;
    delete rnnlm_info_;
    delete rnnlm_to_add_;
    delete rnnlm_to_add_scale_;

    model_->Unref();
    if (spk_model_)
         spk_model_->Unref();
}

void Recognizer::InitState()
{
    endpoint_config_ = model_->endpoint_config_;

    frame_offset_ = 0;
    samples_processed_ = 0;
    samples_round_start_ = 0;

    state_ = RECOGNIZER_INITIALIZED;
}

void Recognizer::InitRescoring()
{
    if (model_->graph_lm_fst_) {

        fst::CacheOptions cache_opts(true, -1);
        fst::ArcMapFstOptions mapfst_opts(cache_opts);
        fst::StdToLatticeMapper<BaseFloat> mapper;

        lm_to_subtract_ = new fst::ArcMapFst<fst::StdArc, LatticeArc, fst::StdToLatticeMapper<BaseFloat> >(*model_->graph_lm_fst_, mapper, mapfst_opts);
        carpa_to_add_ = new ConstArpaLmDeterministicFst(model_->const_arpa_);

        if (model_->rnnlm_enabled_) {
           int lm_order = 4;
           rnnlm_info_ = new kaldi::rnnlm::RnnlmComputeStateInfo(model_->rnnlm_compute_opts, model_->rnnlm, model_->word_embedding_mat);
           rnnlm_to_add_ = new kaldi::rnnlm::KaldiRnnlmDeterministicFst(lm_order, *rnnlm_info_);
           rnnlm_to_add_scale_ = new fst::ScaleDeterministicOnDemandFst(0.5, rnnlm_to_add_);
           carpa_to_add_scale_ = new fst::ScaleDeterministicOnDemandFst(-0.5, carpa_to_add_);
        }
    }
}

void Recognizer::CleanUp()
{
    delete silence_weighting_;
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

    if (decoder_)
       frame_offset_ += decoder_->NumFramesDecoded();

    // Each 10 minutes we drop the pipeline to save frontend memory in continuous processing
    // here we drop few frames remaining in the feature pipeline but hope it will not
    // cause a huge accuracy drop since it happens not very frequently.

    // Also restart if we retrieved final result already

    if (decoder_ == nullptr || state_ == RECOGNIZER_FINALIZED || frame_offset_ > 20000) {
        samples_round_start_ += samples_processed_;
        samples_processed_ = 0;
        frame_offset_ = 0;

        delete decoder_;
        delete feature_pipeline_;

        feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_->feature_info_);
        decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(model_->nnet3_decoding_config_,
            *model_->trans_model_,
            *model_->decodable_info_,
            model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_,
            feature_pipeline_);

        if (spk_model_) {
            delete spk_feature_;
            spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);
        }
    } else {
        decoder_->InitDecoding(frame_offset_);
    }
}

void Recognizer::UpdateSilenceWeights()
{
    if (silence_weighting_->Active() && feature_pipeline_->NumFramesReady() > 0 &&
        feature_pipeline_->IvectorFeature() != nullptr) {
        vector<pair<int32, BaseFloat> > delta_weights;
        silence_weighting_->ComputeCurrentTraceback(decoder_->Decoder());
        silence_weighting_->GetDeltaWeights(feature_pipeline_->NumFramesReady(),
                                          frame_offset_ * 3,
                                          &delta_weights);
        feature_pipeline_->UpdateFrameWeights(delta_weights);
    }
}

void Recognizer::SetMaxAlternatives(int max_alternatives)
{
    max_alternatives_ = max_alternatives;
}

void Recognizer::SetWords(bool words)
{
    words_ = words;
}

void Recognizer::SetPartialWords(bool partial_words)
{
    partial_words_ = partial_words;
}

void Recognizer::SetNLSML(bool nlsml)
{
    nlsml_ = nlsml;
}

void Recognizer::SetEndpointerMode(int mode)
{
    float scale = 1.0;
    switch(mode) {
        case 1:
           scale = 0.75;
           break;
        case 2:
           scale = 1.50;
           break;
        case 3:
           scale = 4.0;
           break;
    }
    KALDI_LOG << "Updating endpointer scale " << scale;
    endpoint_config_ = model_->endpoint_config_;
    endpoint_config_.rule2.min_trailing_silence *= scale;
    endpoint_config_.rule3.min_trailing_silence *= scale;
    endpoint_config_.rule4.min_trailing_silence *= scale;
}

void Recognizer::SetEndpointerDelays(float t_start_max, float t_end, float t_max)
{
    float rule1, rule2, rule3, rule4, rule5;

    rule1 = t_start_max;
    rule2 = t_end;
    rule3 = t_end + 0.5;
    rule4 = t_end + 1.0;
    rule5 = t_max;

    KALDI_LOG << "Updating endpointer delays " << rule1 << "," << rule2 << "," << rule3 << "," << rule4 << "," << rule5;
    endpoint_config_ = model_->endpoint_config_;
    endpoint_config_.rule1.min_trailing_silence = rule1;
    endpoint_config_.rule2.min_trailing_silence = rule2;
    endpoint_config_.rule3.min_trailing_silence = rule3;
    endpoint_config_.rule4.min_trailing_silence = rule4;
    endpoint_config_.rule5.min_utterance_length = rule5;
}


void Recognizer::SetSpkModel(SpkModel *spk_model)
{
    if (state_ == RECOGNIZER_RUNNING) {
        KALDI_ERR << "Can't add speaker model to already running recognizer";
        return;
    }
    spk_model_ = spk_model;
    spk_model_->Ref();
    spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);
}

void Recognizer::SetGrm(char const *grammar)
{
    if (state_ == RECOGNIZER_RUNNING) {
        KALDI_ERR << "Can't add grammar to already running recognizer";
        return;
    }

    if (!model_->hcl_fst_) {
        KALDI_WARN << "Runtime graphs are not supported by this model";
        return;
    }

    delete decode_fst_;

    if (!strcmp(grammar, "[]")) {
        decode_fst_ = LookaheadComposeFst(*model_->hcl_fst_, *model_->g_fst_, model_->disambig_);
    } else {
        UpdateGrammarFst(grammar);
    }

    samples_round_start_ += samples_processed_;
    samples_processed_ = 0;
    frame_offset_ = 0;

    delete decoder_;
    delete feature_pipeline_;
    delete silence_weighting_;

    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);
    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_->feature_info_);
    decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(model_->nnet3_decoding_config_,
            *model_->trans_model_,
            *model_->decodable_info_,
            *decode_fst_,
            feature_pipeline_);

    if (spk_model_) {
        delete spk_feature_;
        spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);
    }

    state_ = RECOGNIZER_INITIALIZED;
}


void Recognizer::UpdateGrammarFst(char const *grammar)
{
    json::JSON obj;
    obj = json::JSON::Load(grammar);

    if (obj.length() <= 0) {
        KALDI_WARN << "Expecting array of strings, got: '" << grammar << "'";
        return;
    }

    KALDI_LOG << obj;

    LanguageModelOptions opts;

    opts.ngram_order = 2;
    opts.discount = 0.5;

    LanguageModelEstimator estimator(opts);
    for (int i = 0; i < obj.length(); i++) {
        bool ok;
        string line = obj[i].ToString(ok);
        if (!ok) {
            KALDI_ERR << "Expecting array of strings, got: '" << obj << "'";
        }

        std::vector<int32> sentence;
        stringstream ss(line);
        string token;
        while (getline(ss, token, ' ')) {
            int32 id = model_->word_syms_->Find(token);
            if (id == kNoSymbol) {
                KALDI_WARN << "Ignoring word missing in vocabulary: '" << token << "'";
            } else {
                sentence.push_back(id);
            }
        }
        estimator.AddCounts(sentence);
    }
    delete g_fst_;
    g_fst_ = new StdVectorFst();
    estimator.Estimate(g_fst_);

    decode_fst_ = LookaheadComposeFst(*model_->hcl_fst_, *g_fst_, model_->disambig_);
}


bool Recognizer::AcceptWaveform(const char *data, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len / 2, kUndefined);
    for (int i = 0; i < len / 2; i++)
        wave(i) = *(((short *)data) + i);
    return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(const short *sdata, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len, kUndefined);
    for (int i = 0; i < len; i++)
        wave(i) = sdata[i];
    return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(const float *fdata, int len)
{
    Vector<BaseFloat> wave;
    wave.Resize(len, kUndefined);
    for (int i = 0; i < len; i++)
        wave(i) = fdata[i];
    return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(Vector<BaseFloat> &wdata)
{
    // Cleanup if we finalized previous utterance or the whole feature pipeline
    if (!(state_ == RECOGNIZER_RUNNING || state_ == RECOGNIZER_INITIALIZED)) {
        CleanUp();
    }
    state_ = RECOGNIZER_RUNNING;

    int step = static_cast<int>(sample_frequency_ * 0.2);
    for (int i = 0; i < wdata.Dim(); i+= step) {
        SubVector<BaseFloat> r = wdata.Range(i, std::min(step, wdata.Dim() - i));
        feature_pipeline_->AcceptWaveform(sample_frequency_, r);
        UpdateSilenceWeights();
        decoder_->AdvanceDecoding();
    }
    samples_processed_ += wdata.Dim();

    if (spk_feature_) {
        spk_feature_->AcceptWaveform(sample_frequency_, wdata);
    }

    if (decoder_->EndpointDetected(endpoint_config_)) {
        return true;
    }

    return false;
}

// Computes an xvector from a chunk of speech features.
static void RunNnetComputation(const MatrixBase<BaseFloat> &features,
    const nnet3::Nnet &nnet, nnet3::CachingOptimizingCompiler *compiler,
    Vector<BaseFloat> *xvector) 
{
    nnet3::ComputationRequest request;
    request.need_model_derivative = false;
    request.store_component_stats = false;
    request.inputs.push_back(
    nnet3::IoSpecification("input", 0, features.NumRows()));
    nnet3::IoSpecification output_spec;
    output_spec.name = "output";
    output_spec.has_deriv = false;
    output_spec.indexes.resize(1);
    request.outputs.resize(1);
    request.outputs[0].Swap(&output_spec);
    shared_ptr<const nnet3::NnetComputation> computation = compiler->Compile(request);
    nnet3::Nnet *nnet_to_update = nullptr;  // we're not doing any update.
    nnet3::NnetComputer computer(nnet3::NnetComputeOptions(), *computation,
                    nnet, nnet_to_update);
    CuMatrix<BaseFloat> input_feats_cu(features);
    computer.AcceptInput("input", &input_feats_cu);
    computer.Run();
    CuMatrix<BaseFloat> cu_output;
    computer.GetOutputDestructive("output", &cu_output);
    xvector->Resize(cu_output.NumCols());
    xvector->CopyFromVec(cu_output.Row(0));
}

#define MIN_SPK_FEATS 50

bool Recognizer::GetSpkVector(Vector<BaseFloat> &out_xvector, int *num_spk_frames)
{
    vector<int32> nonsilence_frames;
    if (silence_weighting_->Active() && feature_pipeline_->NumFramesReady() > 0) {
        silence_weighting_->ComputeCurrentTraceback(decoder_->Decoder(), true);
        silence_weighting_->GetNonsilenceFrames(feature_pipeline_->NumFramesReady(),
                                          frame_offset_ * 3,
                                          &nonsilence_frames);
    }

    int num_frames = spk_feature_->NumFramesReady() - frame_offset_ * 3;
    Matrix<BaseFloat> mfcc(num_frames, spk_feature_->Dim());

    // Not very efficient, would be nice to have faster search
    int num_nonsilence_frames = 0;
    Vector<BaseFloat> feat(spk_feature_->Dim());

    for (int i = 0; i < num_frames; ++i) {
       if (std::find(nonsilence_frames.begin(),
                     nonsilence_frames.end(), i / 3) == nonsilence_frames.end()) {
           continue;
       }

       spk_feature_->GetFrame(i + frame_offset_ * 3, &feat);
       mfcc.CopyRowFromVec(feat, num_nonsilence_frames);
       num_nonsilence_frames++;
    }

    *num_spk_frames = num_nonsilence_frames;

    // Don't extract vector if not enough data
    if (num_nonsilence_frames < MIN_SPK_FEATS) {
        return false;
    }

    mfcc.Resize(num_nonsilence_frames, spk_feature_->Dim(), kCopyData);

    SlidingWindowCmnOptions cmvn_opts;
    cmvn_opts.center = true;
    cmvn_opts.cmn_window = 300;
    Matrix<BaseFloat> features(mfcc.NumRows(), mfcc.NumCols(), kUndefined);
    SlidingWindowCmn(cmvn_opts, mfcc, &features);

    nnet3::NnetSimpleComputationOptions opts;
    nnet3::CachingOptimizingCompilerOptions compiler_config;
    nnet3::CachingOptimizingCompiler compiler(spk_model_->speaker_nnet, opts.optimize_config, compiler_config);

    Vector<BaseFloat> xvector;
    RunNnetComputation(features, spk_model_->speaker_nnet, &compiler, &xvector);

    // Whiten the vector with global mean and transform and normalize mean
    xvector.AddVec(-1.0, spk_model_->mean);

    out_xvector.Resize(spk_model_->transform.NumRows(), kSetZero);
    out_xvector.AddMatVec(1.0, spk_model_->transform, kNoTrans, xvector, 0.0);

    BaseFloat norm = out_xvector.Norm(2.0);
    BaseFloat ratio = norm / sqrt(out_xvector.Dim()); // how much larger it is
                                                  // than it would be, in
                                                  // expectation, if normally
    out_xvector.Scale(1.0 / ratio);

    return true;
}

// If we can't align, we still need to prepare for MBR
static void CopyLatticeForMbr(CompactLattice &lat, CompactLattice *lat_out)
{
    *lat_out = lat;
    RmEpsilon(lat_out, true);
    fst::CreateSuperFinal(lat_out);
    TopSortCompactLatticeIfNeeded(lat_out);
}

const char *Recognizer::MbrResult(CompactLattice &rlat)
{

    CompactLattice aligned_lat;
    if (model_->winfo_) {
        WordAlignLattice(rlat, *model_->trans_model_, *model_->winfo_, 0, &aligned_lat);
    } else {
        CopyLatticeForMbr(rlat, &aligned_lat);
    }

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

        if (words_) {
            word["word"] = model_->word_syms_->Find(words[i]);
            word["start"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + times[i].first) * 0.03;
            word["end"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + times[i].second) * 0.03;
            word["conf"] = conf[i];
            obj["result"].append(word);
        }

        if (i) {
            text << " ";
        }
        text << model_->word_syms_->Find(words[i]);
    }
    obj["text"] = text.str();

    if (spk_model_) {
        Vector<BaseFloat> xvector;
        int num_spk_frames;
        if (GetSpkVector(xvector, &num_spk_frames)) {
            for (int i = 0; i < xvector.Dim(); i++) {
                obj["spk"].append(xvector(i));
            }
            obj["spk_frames"] = num_spk_frames;
        }
    }

    return StoreReturn(obj.dump());
}

static bool CompactLatticeToWordAlignmentWeight(const CompactLattice &clat,
                                                std::vector<int32> *words,
                                                std::vector<int32> *begin_times,
                                                std::vector<int32> *lengths,
                                                CompactLattice::Weight *tot_weight_out)
{
  typedef CompactLattice::Arc Arc;
  typedef Arc::Label Label;
  typedef CompactLattice::StateId StateId;
  typedef CompactLattice::Weight Weight;
  using namespace fst;

  words->clear();
  begin_times->clear();
  lengths->clear();
  *tot_weight_out = Weight::Zero();

  StateId state = clat.Start();
  Weight tot_weight = Weight::One();

  int32 cur_time = 0;
  if (state == kNoStateId) {
    KALDI_WARN << "Empty lattice.";
    return false;
  }
  while (1) {
    Weight final = clat.Final(state);
    size_t num_arcs = clat.NumArcs(state);
    if (final != Weight::Zero()) {
      if (num_arcs != 0) {
        KALDI_WARN << "Lattice is not linear.";
        return false;
      }
      if (!final.String().empty()) {
        KALDI_WARN << "Lattice has alignments on final-weight: probably "
            "was not word-aligned (alignments will be approximate)";
      }
      tot_weight = Times(final, tot_weight);
      *tot_weight_out = tot_weight;
      return true;
    } else {
      if (num_arcs != 1) {
        KALDI_WARN << "Lattice is not linear: num-arcs = " << num_arcs;
        return false;
      }
      fst::ArcIterator<CompactLattice> aiter(clat, state);
      const Arc &arc = aiter.Value();
      Label word_id = arc.ilabel; // Note: ilabel==olabel, since acceptor.
      // Also note: word_id may be zero; we output it anyway.
      int32 length = arc.weight.String().size();
      words->push_back(word_id);
      begin_times->push_back(cur_time);
      lengths->push_back(length);
      tot_weight = Times(arc.weight, tot_weight);
      cur_time += length;
      state = arc.nextstate;
    }
  }
}


const char *Recognizer::NbestResult(CompactLattice &clat)
{
    Lattice lat;
    Lattice nbest_lat;
    std::vector<Lattice> nbest_lats;

    ConvertLattice (clat, &lat);
    fst::ShortestPath(lat, &nbest_lat, max_alternatives_);
    fst::ConvertNbestToVector(nbest_lat, &nbest_lats);

    json::JSON obj;
    for (int k = 0; k < nbest_lats.size(); k++) {

      Lattice nlat = nbest_lats[k];

      CompactLattice nclat;
      fst::Invert(&nlat);
      DeterminizeLattice(nlat, &nclat);

      CompactLattice aligned_nclat;
      if (model_->winfo_) {
          WordAlignLattice(nclat, *model_->trans_model_, *model_->winfo_, 0, &aligned_nclat);
      } else {
          aligned_nclat = nclat;
      }

      std::vector<int32> words;
      std::vector<int32> begin_times;
      std::vector<int32> lengths;
      CompactLattice::Weight weight;

      CompactLatticeToWordAlignmentWeight(aligned_nclat, &words, &begin_times, &lengths, &weight);
      float likelihood = -(weight.Weight().Value1() + weight.Weight().Value2());

      stringstream text;
      json::JSON entry;

      for (int i = 0, first = 1; i < words.size(); i++) {
        json::JSON word;
        if (words[i] == 0)
            continue;
        if (words_) {
            word["word"] = model_->word_syms_->Find(words[i]);
            word["start"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + begin_times[i]) * 0.03;
            word["end"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + begin_times[i] + lengths[i]) * 0.03;
            entry["result"].append(word);
        }

        if (first)
          first = 0;
        else
          text << " ";

        text << model_->word_syms_->Find(words[i]);
      }

      entry["text"] = text.str();
      entry["confidence"]= likelihood;
      obj["alternatives"].append(entry);
    }

    if (spk_model_) {
        Vector<BaseFloat> xvector;
        int num_spk_frames;
        if (GetSpkVector(xvector, &num_spk_frames)) {
            for (int i = 0; i < xvector.Dim(); i++) {
                obj["spk"].append(xvector(i));
            }
            obj["spk_frames"] = num_spk_frames;
        }
    }

    return StoreReturn(obj.dump());
}

const char *Recognizer::NlsmlResult(CompactLattice &clat)
{
    Lattice lat;
    Lattice nbest_lat;
    std::vector<Lattice> nbest_lats;

    ConvertLattice (clat, &lat);
    fst::ShortestPath(lat, &nbest_lat, max_alternatives_);
    fst::ConvertNbestToVector(nbest_lat, &nbest_lats);

    std::stringstream ss;
    ss << "<?xml version=\"1.0\"?>\n";
    ss << "<result grammar=\"default\">\n";

    for (int k = 0; k < nbest_lats.size(); k++) {

      Lattice nlat = nbest_lats[k];

      CompactLattice nclat;
      fst::Invert(&nlat);
      DeterminizeLattice(nlat, &nclat);

      CompactLattice aligned_nclat;
      if (model_->winfo_) {
          WordAlignLattice(nclat, *model_->trans_model_, *model_->winfo_, 0, &aligned_nclat);
      } else {
          aligned_nclat = nclat;
      }

      std::vector<int32> words;
      std::vector<int32> begin_times;
      std::vector<int32> lengths;
      CompactLattice::Weight weight;

      CompactLatticeToWordAlignmentWeight(aligned_nclat, &words, &begin_times, &lengths, &weight);
      float likelihood = -(weight.Weight().Value1() + weight.Weight().Value2());

      stringstream text;
      for (int i = 0, first = 1; i < words.size(); i++) {
        if (words[i] == 0)
            continue;

        if (first)
          first = 0;
        else
          text << " ";

        text << model_->word_syms_->Find(words[i]);
      }

      ss << "<interpretation grammar=\"default\" confidence=\"" << likelihood << "\">\n";
      ss << "<input mode=\"speech\">" << text.str() << "</input>\n";
      ss << "<instance>" << text.str() << "</instance>\n";
      ss << "</interpretation>\n";
    }
    ss << "</result>\n";

    return StoreReturn(ss.str());
}

const char* Recognizer::GetResult()
{
    if (decoder_->NumFramesDecoded() == 0) {
        return StoreEmptyReturn();
    }

    // Original from decoder, subtracted graph weight, rescored with carpa, rescored with rnnlm
    CompactLattice clat, slat, tlat, rlat;

    clat = decoder_->GetLattice(decoder_->NumFramesDecoded(), true);

    if (lm_to_subtract_ && carpa_to_add_) {
        Lattice lat, composed_lat;

        // Delete old score
        ConvertLattice(clat, &lat);
        fst::ScaleLattice(fst::GraphLatticeScale(-1.0), &lat);
        fst::Compose(lat, *lm_to_subtract_, &composed_lat);
        fst::Invert(&composed_lat);
        DeterminizeLattice(composed_lat, &slat);
        fst::ScaleLattice(fst::GraphLatticeScale(-1.0), &slat);

        // Add CARPA score
        TopSortCompactLatticeIfNeeded(&slat);
        ComposeCompactLatticeDeterministic(slat, carpa_to_add_, &tlat);

        // Rescore with RNNLM score on top if needed
        if (rnnlm_to_add_scale_) {
             ComposeLatticePrunedOptions compose_opts;
             compose_opts.lattice_compose_beam = 3.0;
             compose_opts.max_arcs = 3000;
             fst::ComposeDeterministicOnDemandFst<StdArc> combined_rnnlm(carpa_to_add_scale_, rnnlm_to_add_scale_);

             TopSortCompactLatticeIfNeeded(&tlat);
             ComposeCompactLatticePruned(compose_opts, tlat,
                                         &combined_rnnlm, &rlat);
             rnnlm_to_add_->Clear();
        } else {
             rlat = tlat;
        }
    } else {
        rlat = clat;
    }

    // Pruned composition can return empty lattice. It should be rare
    if (rlat.Start() != 0) {
       return StoreEmptyReturn();
    }

    // Apply rescoring weight
    fst::ScaleLattice(fst::GraphLatticeScale(0.9), &rlat);

    if (max_alternatives_ == 0) {
        return MbrResult(rlat);
    } else if (nlsml_) {
        return NlsmlResult(rlat);
    } else {
        return NbestResult(rlat);
    }

}


const char* Recognizer::PartialResult()
{
    if (state_ != RECOGNIZER_RUNNING) {
        return StoreEmptyReturn();
    }

    json::JSON res;

    if (partial_words_) {

        if (decoder_->NumFramesInLattice() == 0) {
            res["partial"] = "";
            return StoreReturn(res.dump());
        }

        CompactLattice clat;
        CompactLattice aligned_lat;

        clat = decoder_->GetLattice(decoder_->NumFramesInLattice(), false);
        if (model_->winfo_) {
            WordAlignLatticePartial(clat, *model_->trans_model_, *model_->winfo_, 0, &aligned_lat);
        } else {
            CopyLatticeForMbr(clat, &aligned_lat);
        }

        MinimumBayesRisk mbr(aligned_lat);
        const vector<BaseFloat> &conf = mbr.GetOneBestConfidences();
        const vector<int32> &words = mbr.GetOneBest();
        const vector<pair<BaseFloat, BaseFloat> > &times = mbr.GetOneBestTimes();

        int size = words.size();

        stringstream text;

        // Create JSON object
        for (int i = 0; i < size; i++) {
            json::JSON word;

            word["word"] = model_->word_syms_->Find(words[i]);
            word["start"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + times[i].first) * 0.03;
            word["end"] = samples_round_start_ / sample_frequency_ + (frame_offset_ + times[i].second) * 0.03;
            word["conf"] = conf[i];
            res["partial_result"].append(word);

            if (i) {
                text << " ";
            }
            text << model_->word_syms_->Find(words[i]);
        }
        res["partial"] = text.str();

    } else {

        if (decoder_->NumFramesDecoded() == 0) {
            res["partial"] = "";
            return StoreReturn(res.dump());
        }
        Lattice lat;
        decoder_->GetBestPath(false, &lat);
        vector<kaldi::int32> alignment, words;
        LatticeWeight weight;
        GetLinearSymbolSequence(lat, &alignment, &words, &weight);

        ostringstream text;
        for (size_t i = 0; i < words.size(); i++) {
            if (i) {
                text << " ";
            }
            text << model_->word_syms_->Find(words[i]);
        }
        res["partial"] = text.str();
    }

    return StoreReturn(res.dump());
}

const char* Recognizer::Result()
{
    if (state_ != RECOGNIZER_RUNNING) {
        return StoreEmptyReturn();
    }
    decoder_->FinalizeDecoding();
    state_ = RECOGNIZER_ENDPOINT;
    return GetResult();
}

const char* Recognizer::FinalResult()
{
    if (state_ != RECOGNIZER_RUNNING) {
        return StoreEmptyReturn();
    }

    feature_pipeline_->InputFinished();
    UpdateSilenceWeights();
    decoder_->AdvanceDecoding();
    decoder_->FinalizeDecoding();
    state_ = RECOGNIZER_FINALIZED;
    GetResult();

    // Free some memory while we are finalized, next
    // iteration will reinitialize them anyway
    delete decoder_;
    delete feature_pipeline_;
    delete silence_weighting_;
    delete spk_feature_;

    feature_pipeline_ = nullptr;
    silence_weighting_ = nullptr;
    decoder_ = nullptr;
    spk_feature_ = nullptr;

    return last_result_.c_str();
}

void Recognizer::Reset()
{
    if (state_ == RECOGNIZER_RUNNING) {
        decoder_->FinalizeDecoding();
    }
    StoreEmptyReturn();
    state_ = RECOGNIZER_ENDPOINT;
}

const char *Recognizer::StoreEmptyReturn()
{
    if (!max_alternatives_) {
        return StoreReturn("{\"text\": \"\"}");
    } else if (nlsml_) {
        return StoreReturn("<?xml version=\"1.0\"?>\n"
                           "<result grammar=\"default\">\n"
                           "<interpretation confidence=\"1.0\">\n"
                           "<instance/>\n"
                           "<input><noinput/></input>\n"
                           "</interpretation>\n"
                           "</result>\n");
    } else {
        return StoreReturn("{\"alternatives\" : [{\"text\": \"\", \"confidence\" : 1.0}] }");
    }
}

// Store result in recognizer and return as const string
const char *Recognizer::StoreReturn(const string &res)
{
    last_result_ = res;
    return last_result_.c_str();
}
