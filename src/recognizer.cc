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
#include "fstext/fstext-utils.h"
#include "json.h"
#include "language_model.h"
#include "lat/sausages.h"

using namespace fst;
using namespace kaldi::nnet3;

Recognizer::Recognizer(Model *model, float sample_frequency)
    : model_(model), spk_model_(0), sample_frequency_(sample_frequency) {

  model_->Ref();

  feature_pipeline_ =
      new kaldi::OnlineNnet2FeaturePipeline(model_->feature_info_);
  silence_weighting_ = new kaldi::OnlineSilenceWeighting(
      *model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

  if (!model_->hclg_fst_) {
    if (GetHclFst() && model_->g_fst_) {
      decode_fst_ =
          LookaheadComposeFst(*GetHclFst(), *model_->g_fst_, *GetDisambig());
    } else {
      KALDI_ERR << "Can't create decoding graph";
    }
  }

  decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(
      model_->nnet3_decoding_config_, *model_->trans_model_,
      *model_->decodable_info_,
      model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_, feature_pipeline_);

  InitState();
  InitRescoring();
}

Recognizer::Recognizer(Model *model, float sample_frequency,
                       char const *grammar)
    : model_(model), spk_model_(0), sample_frequency_(sample_frequency) {
  model_->Ref();

  feature_pipeline_ =
      new kaldi::OnlineNnet2FeaturePipeline(model_->feature_info_);
  silence_weighting_ = new kaldi::OnlineSilenceWeighting(
      *model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

  if (model_->hcl_fst_) {
    UpdateGrammarFst(grammar);
  } else {
    KALDI_WARN << "Runtime graphs are not supported by this model";
  }

  decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(
      model_->nnet3_decoding_config_, *model_->trans_model_,
      *model_->decodable_info_,
      model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_, feature_pipeline_);

  InitState();
  InitRescoring();
}

Recognizer::Recognizer(Model *model, float sample_frequency,
                       SpkModel *spk_model)
    : model_(model), spk_model_(spk_model),
      sample_frequency_(sample_frequency) {

  model_->Ref();
  spk_model->Ref();

  feature_pipeline_ =
      new kaldi::OnlineNnet2FeaturePipeline(model_->feature_info_);
  silence_weighting_ = new kaldi::OnlineSilenceWeighting(
      *model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

  if (!model_->hclg_fst_) {
    if (model_->hcl_fst_ && model_->g_fst_) {
      decode_fst_ =
          LookaheadComposeFst(*GetHclFst(), *model_->g_fst_, *GetDisambig());
    } else {
      KALDI_ERR << "Can't create decoding graph";
    }
  }

  decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(
      model_->nnet3_decoding_config_, *model_->trans_model_,
      *model_->decodable_info_,
      model_->hclg_fst_ ? *model_->hclg_fst_ : *decode_fst_, feature_pipeline_);

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

void Recognizer::InitState() {
  frame_offset_ = 0;
  samples_processed_ = 0;
  samples_round_start_ = 0;

  state_ = RECOGNIZER_INITIALIZED;
}

void Recognizer::InitRescoring() {
  if (model_->graph_lm_fst_) {

    fst::CacheOptions cache_opts(true, -1);
    fst::ArcMapFstOptions mapfst_opts(cache_opts);
    fst::StdToLatticeMapper<BaseFloat> mapper;

    lm_to_subtract_ = new fst::ArcMapFst<fst::StdArc, LatticeArc,
                                         fst::StdToLatticeMapper<BaseFloat>>(
        *model_->graph_lm_fst_, mapper, mapfst_opts);
    carpa_to_add_ = new ConstArpaLmDeterministicFst(model_->const_arpa_);

    if (model_->rnnlm_enabled_) {
      int lm_order = 4;
      rnnlm_info_ = new kaldi::rnnlm::RnnlmComputeStateInfo(
          model_->rnnlm_compute_opts, model_->rnnlm,
          model_->word_embedding_mat);
      rnnlm_to_add_ =
          new kaldi::rnnlm::KaldiRnnlmDeterministicFst(lm_order, *rnnlm_info_);
      rnnlm_to_add_scale_ =
          new fst::ScaleDeterministicOnDemandFst(0.5, rnnlm_to_add_);
      carpa_to_add_scale_ =
          new fst::ScaleDeterministicOnDemandFst(-0.5, carpa_to_add_);
    }
  }
}

void Recognizer::CleanUp() {
  delete silence_weighting_;
  silence_weighting_ = new kaldi::OnlineSilenceWeighting(
      *model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);

  if (decoder_)
    frame_offset_ += decoder_->NumFramesDecoded();

  // Each 10 minutes we drop the pipeline to save frontend memory in continuous
  // processing here we drop few frames remaining in the feature pipeline but
  // hope it will not cause a huge accuracy drop since it happens not very
  // frequently.

  // Also restart if we retrieved final result already

  if (decoder_ == nullptr || state_ == RECOGNIZER_FINALIZED ||
      frame_offset_ > 20000) {
    samples_round_start_ += samples_processed_;
    samples_processed_ = 0;
    frame_offset_ = 0;

    delete decoder_;
    delete feature_pipeline_;

    feature_pipeline_ =
        new kaldi::OnlineNnet2FeaturePipeline(model_->feature_info_);
    decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(
        model_->nnet3_decoding_config_, *model_->trans_model_,
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

void Recognizer::UpdateSilenceWeights() {
  if (silence_weighting_->Active() && feature_pipeline_->NumFramesReady() > 0 &&
      feature_pipeline_->IvectorFeature() != nullptr) {
    vector<pair<int32, BaseFloat>> delta_weights;
    silence_weighting_->ComputeCurrentTraceback(decoder_->Decoder());
    silence_weighting_->GetDeltaWeights(feature_pipeline_->NumFramesReady(),
                                        frame_offset_ * 3, &delta_weights);
    feature_pipeline_->UpdateFrameWeights(delta_weights);
  }
}

void Recognizer::SetMaxAlternatives(int max_alternatives) {
  max_alternatives_ = max_alternatives;
}

void Recognizer::SetWords(bool words) { words_ = words; }

void Recognizer::SetPartialWords(bool partial_words) {
  partial_words_ = partial_words;
}

void Recognizer::SetNLSML(bool nlsml) { nlsml_ = nlsml; }

void Recognizer::SetSpkModel(SpkModel *spk_model) {
  if (state_ == RECOGNIZER_RUNNING) {
    KALDI_ERR << "Can't add speaker model to already running recognizer";
    return;
  }
  spk_model_ = spk_model;
  spk_model_->Ref();
  spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);
}

void Recognizer::SetGrm(char const *grammar, const char *const *words,
                        const char *const *pronunciations, int num_words) {
  if (state_ == RECOGNIZER_RUNNING) {
    KALDI_ERR << "Can't add speaker model to already running recognizer";
    return;
  }

  if (!model_->hcl_fst_) {
    KALDI_WARN << "Runtime graphs are not supported by this model";
    return;
  }

  if (!strcmp(grammar, "[]")) {
    delete hcl_fst_;
    delete disambig_;
    delete decode_fst_;
    decode_fst_ =
        LookaheadComposeFst(*GetHclFst(), *model_->g_fst_, *GetDisambig());
  } else {
    // Update HCLr fst if needed
    if (num_words > 0 && words != nullptr && pronunciations != nullptr) {
      KALDI_LOG << "Rebuilding lexicon with " << num_words << " words";
      vector<string> words_vec(words, words + num_words);
      vector<string> pronunciations_vec(pronunciations,
                                        pronunciations + num_words);
      auto t0 = chrono::high_resolution_clock::now();
      RebuildLexicon(words_vec, pronunciations_vec);
      if (GetHclFst() == nullptr) {
        KALDI_ERR << "Failed to rebuild lexicon";
        return;
      }
      auto t1 = chrono::high_resolution_clock::now();
      auto duration =
          chrono::duration_cast<chrono::milliseconds>(t1 - t0).count();
      KALDI_LOG << "Rebuilding lexicon done in " << duration << "ms";
    }
    // Update grammar fst
    delete decode_fst_;
    UpdateGrammarFst(grammar);
  }

  samples_round_start_ += samples_processed_;
  samples_processed_ = 0;
  frame_offset_ = 0;

  delete decoder_;
  delete feature_pipeline_;
  delete silence_weighting_;

  silence_weighting_ = new kaldi::OnlineSilenceWeighting(
      *model_->trans_model_, model_->feature_info_.silence_weighting_config, 3);
  feature_pipeline_ =
      new kaldi::OnlineNnet2FeaturePipeline(model_->feature_info_);
  decoder_ = new kaldi::SingleUtteranceNnet3IncrementalDecoder(
      model_->nnet3_decoding_config_, *model_->trans_model_,
      *model_->decodable_info_, *decode_fst_, feature_pipeline_);

  if (spk_model_) {
    delete spk_feature_;
    spk_feature_ = new OnlineMfcc(spk_model_->spkvector_mfcc_opts);
  }

  state_ = RECOGNIZER_INITIALIZED;
}

void Recognizer::UpdateGrammarFst(char const *grammar) {
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
  g_fst_ = new StdVectorFst();
  estimator.Estimate(g_fst_);

  decode_fst_ = LookaheadComposeFst(*GetHclFst(), *g_fst_, *GetDisambig());
}

bool Recognizer::AcceptWaveform(const char *data, int len) {
  Vector<BaseFloat> wave;
  wave.Resize(len / 2, kUndefined);
  for (int i = 0; i < len / 2; i++)
    wave(i) = *(((short *)data) + i);
  return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(const short *sdata, int len) {
  Vector<BaseFloat> wave;
  wave.Resize(len, kUndefined);
  for (int i = 0; i < len; i++)
    wave(i) = sdata[i];
  return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(const float *fdata, int len) {
  Vector<BaseFloat> wave;
  wave.Resize(len, kUndefined);
  for (int i = 0; i < len; i++)
    wave(i) = fdata[i];
  return AcceptWaveform(wave);
}

bool Recognizer::AcceptWaveform(Vector<BaseFloat> &wdata) {
  // Cleanup if we finalized previous utterance or the whole feature pipeline
  if (!(state_ == RECOGNIZER_RUNNING || state_ == RECOGNIZER_INITIALIZED)) {
    CleanUp();
  }
  state_ = RECOGNIZER_RUNNING;

  int step = static_cast<int>(sample_frequency_ * 0.2);
  for (int i = 0; i < wdata.Dim(); i += step) {
    SubVector<BaseFloat> r = wdata.Range(i, std::min(step, wdata.Dim() - i));
    feature_pipeline_->AcceptWaveform(sample_frequency_, r);
    UpdateSilenceWeights();
    decoder_->AdvanceDecoding();
  }
  samples_processed_ += wdata.Dim();

  if (spk_feature_) {
    spk_feature_->AcceptWaveform(sample_frequency_, wdata);
  }

  if (decoder_->EndpointDetected(model_->endpoint_config_)) {
    return true;
  }

  return false;
}

// Computes an xvector from a chunk of speech features.
static void RunNnetComputation(const MatrixBase<BaseFloat> &features,
                               const nnet3::Nnet &nnet,
                               nnet3::CachingOptimizingCompiler *compiler,
                               Vector<BaseFloat> *xvector) {
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
  shared_ptr<const nnet3::NnetComputation> computation =
      compiler->Compile(request);
  nnet3::Nnet *nnet_to_update = nullptr; // we're not doing any update.
  nnet3::NnetComputer computer(nnet3::NnetComputeOptions(), *computation, nnet,
                               nnet_to_update);
  CuMatrix<BaseFloat> input_feats_cu(features);
  computer.AcceptInput("input", &input_feats_cu);
  computer.Run();
  CuMatrix<BaseFloat> cu_output;
  computer.GetOutputDestructive("output", &cu_output);
  xvector->Resize(cu_output.NumCols());
  xvector->CopyFromVec(cu_output.Row(0));
}

#define MIN_SPK_FEATS 50

bool Recognizer::GetSpkVector(Vector<BaseFloat> &out_xvector,
                              int *num_spk_frames) {
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
    if (std::find(nonsilence_frames.begin(), nonsilence_frames.end(), i / 3) ==
        nonsilence_frames.end()) {
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
  nnet3::CachingOptimizingCompiler compiler(
      spk_model_->speaker_nnet, opts.optimize_config, compiler_config);

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
static void CopyLatticeForMbr(CompactLattice &lat, CompactLattice *lat_out) {
  *lat_out = lat;
  RmEpsilon(lat_out, true);
  fst::CreateSuperFinal(lat_out);
  TopSortCompactLatticeIfNeeded(lat_out);
}

const char *Recognizer::MbrResult(CompactLattice &rlat) {

  CompactLattice aligned_lat;
  if (model_->winfo_) {
    WordAlignLattice(rlat, *model_->trans_model_, *model_->winfo_, 0,
                     &aligned_lat);
  } else {
    CopyLatticeForMbr(rlat, &aligned_lat);
  }

  MinimumBayesRisk mbr(aligned_lat);
  const vector<BaseFloat> &conf = mbr.GetOneBestConfidences();
  const vector<int32> &words = mbr.GetOneBest();
  const vector<pair<BaseFloat, BaseFloat>> &times = mbr.GetOneBestTimes();

  int size = words.size();

  json::JSON obj;
  stringstream text;

  // Create JSON object
  for (int i = 0; i < size; i++) {
    json::JSON word;

    if (words_) {
      word["word"] = model_->word_syms_->Find(words[i]);
      word["start"] = samples_round_start_ / sample_frequency_ +
                      (frame_offset_ + times[i].first) * 0.03;
      word["end"] = samples_round_start_ / sample_frequency_ +
                    (frame_offset_ + times[i].second) * 0.03;
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

static bool CompactLatticeToWordAlignmentWeight(
    const CompactLattice &clat, std::vector<int32> *words,
    std::vector<int32> *begin_times, std::vector<int32> *lengths,
    CompactLattice::Weight *tot_weight_out) {
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

const char *Recognizer::NbestResult(CompactLattice &clat) {
  Lattice lat;
  Lattice nbest_lat;
  std::vector<Lattice> nbest_lats;

  ConvertLattice(clat, &lat);
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
      WordAlignLattice(nclat, *model_->trans_model_, *model_->winfo_, 0,
                       &aligned_nclat);
    } else {
      aligned_nclat = nclat;
    }

    std::vector<int32> words;
    std::vector<int32> begin_times;
    std::vector<int32> lengths;
    CompactLattice::Weight weight;

    CompactLatticeToWordAlignmentWeight(aligned_nclat, &words, &begin_times,
                                        &lengths, &weight);
    float likelihood = -(weight.Weight().Value1() + weight.Weight().Value2());

    stringstream text;
    json::JSON entry;

    for (int i = 0, first = 1; i < words.size(); i++) {
      json::JSON word;
      if (words[i] == 0)
        continue;
      if (words_) {
        word["word"] = model_->word_syms_->Find(words[i]);
        word["start"] = samples_round_start_ / sample_frequency_ +
                        (frame_offset_ + begin_times[i]) * 0.03;
        word["end"] = samples_round_start_ / sample_frequency_ +
                      (frame_offset_ + begin_times[i] + lengths[i]) * 0.03;
        entry["result"].append(word);
      }

      if (first)
        first = 0;
      else
        text << " ";

      text << model_->word_syms_->Find(words[i]);
    }

    entry["text"] = text.str();
    entry["confidence"] = likelihood;
    obj["alternatives"].append(entry);
  }

  return StoreReturn(obj.dump());
}

const char *Recognizer::NlsmlResult(CompactLattice &clat) {
  Lattice lat;
  Lattice nbest_lat;
  std::vector<Lattice> nbest_lats;

  ConvertLattice(clat, &lat);
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
      WordAlignLattice(nclat, *model_->trans_model_, *model_->winfo_, 0,
                       &aligned_nclat);
    } else {
      aligned_nclat = nclat;
    }

    std::vector<int32> words;
    std::vector<int32> begin_times;
    std::vector<int32> lengths;
    CompactLattice::Weight weight;

    CompactLatticeToWordAlignmentWeight(aligned_nclat, &words, &begin_times,
                                        &lengths, &weight);
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

    ss << "<interpretation grammar=\"default\" confidence=\"" << likelihood
       << "\">\n";
    ss << "<input mode=\"speech\">" << text.str() << "</input>\n";
    ss << "<instance>" << text.str() << "</instance>\n";
    ss << "</interpretation>\n";
  }
  ss << "</result>\n";

  return StoreReturn(ss.str());
}

const char *Recognizer::GetResult() {
  if (decoder_->NumFramesDecoded() == 0) {
    return StoreEmptyReturn();
  }

  // Original from decoder, subtracted graph weight, rescored with carpa,
  // rescored with rnnlm
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
      fst::ComposeDeterministicOnDemandFst<StdArc> combined_rnnlm(
          carpa_to_add_scale_, rnnlm_to_add_scale_);

      TopSortCompactLatticeIfNeeded(&tlat);
      ComposeCompactLatticePruned(compose_opts, tlat, &combined_rnnlm, &rlat);
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

const char *Recognizer::PartialResult() {
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
      WordAlignLatticePartial(clat, *model_->trans_model_, *model_->winfo_, 0,
                              &aligned_lat);
    } else {
      CopyLatticeForMbr(clat, &aligned_lat);
    }

    MinimumBayesRisk mbr(aligned_lat);
    const vector<BaseFloat> &conf = mbr.GetOneBestConfidences();
    const vector<int32> &words = mbr.GetOneBest();
    const vector<pair<BaseFloat, BaseFloat>> &times = mbr.GetOneBestTimes();

    int size = words.size();

    stringstream text;

    // Create JSON object
    for (int i = 0; i < size; i++) {
      json::JSON word;

      word["word"] = model_->word_syms_->Find(words[i]);
      word["start"] = samples_round_start_ / sample_frequency_ +
                      (frame_offset_ + times[i].first) * 0.03;
      word["end"] = samples_round_start_ / sample_frequency_ +
                    (frame_offset_ + times[i].second) * 0.03;
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

const char *Recognizer::Result() {
  if (state_ != RECOGNIZER_RUNNING) {
    return StoreEmptyReturn();
  }
  decoder_->FinalizeDecoding();
  state_ = RECOGNIZER_ENDPOINT;
  return GetResult();
}

const char *Recognizer::FinalResult() {
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

void Recognizer::Reset() {
  if (state_ == RECOGNIZER_RUNNING) {
    decoder_->FinalizeDecoding();
  }
  StoreEmptyReturn();
  state_ = RECOGNIZER_ENDPOINT;
}

const char *Recognizer::StoreEmptyReturn() {
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
    return StoreReturn(
        "{\"alternatives\" : [{\"text\": \"\", \"confidence\" : 1.0}] }");
  }
}

// Store result in recognizer and return as const string
const char *Recognizer::StoreReturn(const string &res) {
  last_result_ = res;
  return last_result_.c_str();
}

void Recognizer::RebuildLexicon(std::vector<std::string> &words,
                                std::vector<std::string> &pronunciations) {
  using namespace fst;
  using namespace std;
  using StateId = StdVectorFst::StateId;
  using Weight = StdArc::Weight;
  using Label = StdArc::Label;

  if (words.size() != pronunciations.size()) {
    KALDI_ERR << "Number of words and pronunciations must be equal";
    return;
  }

  if (state_ == RECOGNIZER_RUNNING) {
    KALDI_ERR << "Can't add speaker model to already running recognizer";
    return;
  }

  if (model_->ctx_dep_ == nullptr) {
    KALDI_ERR << "Can't rebuild lexicon without phone symbols and ctx dep tree";
    return;
  }

  // Maybe make this adjustable?:

  string silence_phone = "SIL";
  // At the beginning of sentence and after each word, we output silence with
  // probability 0.5;
  // the probability mass assigned to having no silence is 1.0 - 0.5 = 0.5.
  float silence_prob = 0.5;
  // In mkgraph.sh = 1.0, in training = 0.1, in compile-graph.cc = 0.1
  float self_loop_scale = 1.0;
  // In our current training scripts, this scale is 1.0. This scale only affects
  // the parts of the transitions that do not relate to self-loop probabilities,
  // and in the normal topology (Bakis model) it has no effect at all
  float transition_scale = 1.0;

  Label silence_phone_id = model_->phone_syms_->Find(silence_phone);
  if (silence_phone_id == kNoSymbol) {
    KALDI_ERR << "Silence phone not found in the phone symbol table";
    return;
  }

  // Create a new word symbol table for the new words
  SymbolTable word_syms("words");

  VectorFst<StdArc> l_fst;
  StateId start_state = l_fst.AddState();
  StateId loop_state = l_fst.AddState();
  StateId silence_state = l_fst.AddState();
  l_fst.SetStart(start_state);

  // Add transitions
  float nosil_cost = -log(1.0 - silence_prob);
  float sil_cost = -log(silence_prob);

  l_fst.AddArc(start_state, StdArc(0, 0, Weight(nosil_cost), loop_state));
  l_fst.AddArc(start_state,
               StdArc(silence_phone_id, 0, Weight(sil_cost), silence_state));
  l_fst.AddArc(silence_state,
               StdArc(silence_phone_id, 0, Weight::One(), loop_state));

  l_fst.SetFinal(loop_state, Weight::One());

  // Insert the epsilon symbol at the begining of words and pronunciations
  // In the loop we skip any further `<eps> SIL` pairs
  words.insert(words.begin(), "<eps>");
  pronunciations.insert(pronunciations.begin(), silence_phone);

  // Add a map to store existing pronunciations
  SymbolTable disambiguation_syms("disambiguation");
  unordered_map<string, int64> last_disambiguation_symbol;

  for (size_t i = 0; i < words.size(); ++i) {
    const string &word = words[i];
    const string &pronunciation = pronunciations[i];

    // Skip any manually added epsion entries
    if (i != 0 && word == "<eps>" && pronunciation == silence_phone) {
      continue;
    }

    if (word.empty() || pronunciation.empty()) {
      KALDI_WARN << "Skipping word with empty word or pronunciation in line "
                 << i + 1;
      continue;
    }

    Label word_id = word_syms.AddSymbol(word);

    Label disambiguation_symbol = kNoLabel;
    // Check if pronunciation exists in the map
    if (last_disambiguation_symbol.find(pronunciation) !=
        last_disambiguation_symbol.end()) {
      // Increment the disambiguation symbol counter
      disambiguation_symbol = last_disambiguation_symbol[pronunciation];
      int64 new_disambiguation_number = disambiguation_symbol + 1;
      disambiguation_symbol = disambiguation_syms.AddSymbol(
          "#" + to_string(new_disambiguation_number));
      last_disambiguation_symbol[pronunciation] = new_disambiguation_number;
    } else {
      // Add the pronunciation to the map
      last_disambiguation_symbol[pronunciation] = -1;
    }

    istringstream iss(pronunciation);
    string phone;
    StateId current_state = loop_state;
    bool first_phone = true;
    while (iss >> phone) {
      Label phone_id = model_->phone_syms_->Find(phone);
      if (phone_id == kNoSymbol) {
        KALDI_WARN << "Ignoring phone missing in vocabulary: '" << phone << "'";
        continue;
      }

      StateId next_state_temp = l_fst.AddState();
      Label olabel = first_phone ? word_id : 0;

      if (first_phone && disambiguation_symbol != kNoLabel) {
        current_state = next_state_temp;
        next_state_temp = l_fst.AddState();
        l_fst.AddArc(current_state, StdArc(0, disambiguation_symbol,
                                           Weight::One(), next_state_temp));
      }

      l_fst.AddArc(current_state,
                   StdArc(phone_id, olabel, Weight::One(), next_state_temp));
      current_state = next_state_temp;
      first_phone = false;
    }

    if (current_state != loop_state) {
      if (silence_phone_id != model_->phone_syms_->Find(pronunciation)) {
        l_fst.AddArc(current_state,
                     StdArc(0, 0, Weight(nosil_cost), loop_state));
        l_fst.AddArc(current_state, StdArc(silence_phone_id, 0,
                                           Weight(sil_cost), silence_state));
      } else {
        l_fst.AddArc(current_state, StdArc(0, 0, Weight::One(), loop_state));
      }
    }
  }

  DeterminizeStarInLog(&l_fst);
  ArcSort(&l_fst, StdILabelCompare());

  // Extract phone disambiguation symbols
  // by looking for symbols starting with '#'
  vector<int32> disambig_syms;
  for (int i = 0; i < model_->phone_syms_->NumSymbols(); ++i) {
    const string &symbol = model_->phone_syms_->Find(i);
    if (!symbol.empty() && symbol[0] == '#') {
      disambig_syms.push_back(i);
    }
  }

  int32 context_width = model_->ctx_dep_->ContextWidth();
  int32 central_position = model_->ctx_dep_->CentralPosition();

  vector<vector<int32>> ilabels;
  // TODO: Add nonterm stuff
  VectorFst<StdArc> cl_fst;
  ComposeContext(disambig_syms, context_width, central_position, &l_fst,
                 &cl_fst, &ilabels);
  ArcSort(&cl_fst, StdILabelCompare());

  // Create H transducer
  HTransducerConfig h_cfg;
  h_cfg.transition_scale = transition_scale;
  // Must be >= 0 for grammar fst
  h_cfg.nonterm_phones_offset = -1;
  // disambiguation symbols on the input side of H
  vector<int32> *disambig_syms_h = new vector<int32>();
  VectorFst<StdArc> *h_fst =
      GetHTransducer(ilabels, *model_->ctx_dep_, *model_->trans_model_, h_cfg,
                     disambig_syms_h);

  ArcSort(h_fst, StdOLabelCompare());

  // Compose HCL transducer
  VectorFst<StdArc> composed_fst;
  // TableCompose(*h_fst, cl_fst, &composed_fst);
  Compose(*h_fst, cl_fst, &composed_fst);
  delete h_fst;

  // Epsilon-removal and determinization combined.
  // This will fail if not determinizable.
  DeterminizeStarInLog(&composed_fst);

  if (!disambig_syms_h->empty()) {
    RemoveSomeInputSymbols(*disambig_syms_h, &composed_fst);
    RemoveEpsLocal(&composed_fst);
  }

  bool check_no_self_loops = true, reorder = true;
  AddSelfLoops(*model_->trans_model_, *disambig_syms_h, self_loop_scale,
               reorder, check_no_self_loops, &composed_fst);

  ArcSort(&composed_fst, StdOLabelCompare());

  // Create the olabel lookahead matcher
  vector<pair<Label, Label>> relabel;
  StdOLabelLookAheadFst lcomposed_fst(composed_fst);

  // Get the relabel pairs
  LabelLookAheadRelabeler<StdArc>::RelabelPairs(lcomposed_fst, &relabel);

  // Print the relabel pairs
  SymbolTable *relabeled_word_syms = new SymbolTable("words");
  // Go through word_syms_ and relabel the words
  for (int i = 0; i < word_syms.NumSymbols(); ++i) {
    string word = word_syms.Find(i);
    // Check if the word is in the relabel map
    Label wid = i;
    for (const auto &pair : relabel) {
      if (pair.first == i) {
        wid = pair.second;
        break;
      }
    }
    relabeled_word_syms->AddSymbol(word, wid);
  }

  // Switch HCLr, word_syms_ and disambig_ with new variables
  delete hcl_fst_;
  hcl_fst_ = lcomposed_fst.Copy(false);

  delete word_syms_;
  word_syms_ = relabeled_word_syms;

  delete disambig_;
  disambig_ = disambig_syms_h;
}

string Recognizer::FindWord(int64 word_id) {
  string word = word_syms_ ? word_syms_->Find(word_id)
                           : model_->word_syms_->Find(word_id);
  return word;
}

int64 Recognizer::FindWordId(const string &word) {
  return word_syms_ ? word_syms_->Find(word) : model_->word_syms_->Find(word);
}

fst::Fst<fst::StdArc> *Recognizer::GetHclFst() {
  if (hcl_fst_ == nullptr) {
    return model_->hcl_fst_;
  }
  return hcl_fst_;
}

std::vector<int32> *Recognizer::GetDisambig() {
  if (disambig_ == nullptr) {
    return &model_->disambig_;
  }
  return disambig_;
}