#include "kaldi_recognizer.h"

#include "fstext/fstext-utils.h"
#include "lat/sausages.h"

using namespace fst;
using namespace kaldi::nnet3;

template<class Arc>
ComposeFst<Arc> *TableComposeFst(
    const Fst<Arc> &ifst1, const Fst<Arc> &ifst2) {
  typedef LookAheadMatcher< StdFst > M;
  typedef AltSequenceComposeFilter<M> SF;
  typedef LookAheadComposeFilter<SF, M>  LF;
  typedef PushWeightsComposeFilter<LF, M> WF;
  typedef PushLabelsComposeFilter<WF, M> ComposeFilter;
  typedef M FstMatcher;

  fst::CacheOptions cache_opts(true, 1 << 26LL);
  ComposeFstOptions<StdArc, FstMatcher, ComposeFilter> opts(cache_opts);

  return new ComposeFst<Arc>(ifst1, ifst2, opts);
}

KaldiRecognizer::KaldiRecognizer(Model &model) : model_(model) {

    feature_pipeline_ = new kaldi::OnlineNnet2FeaturePipeline (model_.feature_info_);
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_.trans_model_, model_.feature_info_.silence_weighting_config, 3);

    decode_fst_ = TableComposeFst(*model_.hcl_fst_, *model_.g_fst_);

    decoder_ = new kaldi::SingleUtteranceNnet3Decoder(model_.nnet3_decoding_config_,
            *model_.trans_model_,
            *model_.decodable_info_,
            *decode_fst_,
            feature_pipeline_);

    frame_offset = 0;
    input_finalized_ = false;
}

KaldiRecognizer::~KaldiRecognizer() {
    delete feature_pipeline_;
    delete silence_weighting_;
    delete decode_fst_;
    delete decoder_;
}

void KaldiRecognizer::CleanUp()
{
    delete silence_weighting_;
    silence_weighting_ = new kaldi::OnlineSilenceWeighting(*model_.trans_model_, model_.feature_info_.silence_weighting_config, 3);

    frame_offset += decoder_->NumFramesDecoded();
    decoder_->InitDecoding(frame_offset);
}

void KaldiRecognizer::UpdateSilenceWeights()
{
    if (silence_weighting_->Active() && feature_pipeline_->NumFramesReady() > 0 &&
        feature_pipeline_->IvectorFeature() != NULL) {
        std::vector<std::pair<int32, BaseFloat> > delta_weights;
        silence_weighting_->ComputeCurrentTraceback(decoder_->Decoder());
        silence_weighting_->GetDeltaWeights(feature_pipeline_->NumFramesReady(),
                                          frame_offset * 3,
                                          &delta_weights);
        feature_pipeline_->UpdateFrameWeights(delta_weights);
    }
}

bool KaldiRecognizer::AcceptWaveform(const char *data, int len) 
{

    if (input_finalized_) {
        CleanUp();
        input_finalized_ = false;
    }

    Vector<BaseFloat> wave;
    wave.Resize(len / 2, kUndefined);
    for (int i = 0; i < len / 2; i++)
        wave(i) = *(((short *)data) + i);

    feature_pipeline_->AcceptWaveform(16000, wave);
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
    WordAlignLattice(clat, *model_.trans_model_, *model_.winfo_, 0, &aligned_lat);
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
        ss << "{\"word\": \"" << model_.word_syms_->Find(words[i]) << "\", \"start\" : " << times[i].first << "," <<
                " \"end\" : " << times[i].second << ", \"conf\" : " << conf[i] << "}";
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
