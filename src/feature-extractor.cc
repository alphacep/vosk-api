// features.cc
//
// Copyright (c)  2023  Xiaomi Corporation

#include "feature-extractor.h"

#include <algorithm>
#include <memory>
#include <mutex>  // NOLINT
#include <sstream>
#include <vector>
#include <iostream>

#include "online-feature.h"
#include "macros.h"
#include "resample.h"

namespace sherpa_onnx {

void FeatureExtractorConfig::Register(ParseOptions *po) {
  po->Register("sample-rate", &sampling_rate,
               "Sampling rate of the input waveform. "
               "Note: You can have a different "
               "sample rate for the input waveform. We will do resampling "
               "inside the feature extractor");

  po->Register("feat-dim", &feature_dim,
               "Feature dimension. Must match the one expected by the model.");
}

std::string FeatureExtractorConfig::ToString() const {
  std::ostringstream os;

  os << "FeatureExtractorConfig(";
  os << "sampling_rate=" << sampling_rate << ", ";
  os << "feature_dim=" << feature_dim << ")";

  return os.str();
}

class FeatureExtractor::Impl {
 public:
  explicit Impl(const FeatureExtractorConfig &config) : config_(config) {
    opts_.frame_opts.dither = config_.dither;
    opts_.frame_opts.snip_edges = config_.snip_edges;
    opts_.frame_opts.samp_freq = config_.sampling_rate;
    opts_.frame_opts.frame_shift_ms = config_.frame_shift_ms;
    opts_.frame_opts.frame_length_ms = config_.frame_length_ms;
    opts_.frame_opts.remove_dc_offset = config_.remove_dc_offset;
    opts_.frame_opts.preemph_coeff = config_.preemph_coeff;
    opts_.frame_opts.window_type = config_.window_type;
    opts_.frame_opts.round_to_power_of_two = config_.round_to_power_of_two;
    opts_.mel_opts.num_bins = config_.feature_dim;
    opts_.mel_opts.high_freq = config_.high_freq;
    opts_.mel_opts.low_freq = config_.low_freq;

    fbank_ = std::make_unique<knf::OnlineFbank>(opts_);
  }

  void AcceptWaveform(int32_t sampling_rate, const float *waveform, int32_t n) {
    if (config_.normalize_samples) {
      AcceptWaveformImpl(sampling_rate, waveform, n);
    } else {
      std::vector<float> buf(n);
      for (int32_t i = 0; i != n; ++i) {
        buf[i] = waveform[i] * 32768;
      }
      AcceptWaveformImpl(sampling_rate, buf.data(), n);
    }
  }

  void AcceptWaveformImpl(int32_t sampling_rate, const float *waveform,
                          int32_t n) {
    std::lock_guard<std::mutex> lock(mutex_);

    if (resampler_) {
      if (sampling_rate != resampler_->GetInputSamplingRate()) {
        SHERPA_ONNX_LOGE(
            "You changed the input sampling rate!! Expected: %d, given: "
            "%d",
            resampler_->GetInputSamplingRate(), sampling_rate);
        exit(-1);
      }

      std::vector<float> samples;
      resampler_->Resample(waveform, n, false, &samples);
      fbank_->AcceptWaveform(opts_.frame_opts.samp_freq, samples.data(),
                             samples.size());
      return;
    }

    if (sampling_rate != opts_.frame_opts.samp_freq) {
      SHERPA_ONNX_LOGE(
          "Creating a resampler:\n"
          "   in_sample_rate: %d\n"
          "   output_sample_rate: %d\n",
          sampling_rate, static_cast<int32_t>(opts_.frame_opts.samp_freq));

      float min_freq =
          std::min<int32_t>(sampling_rate, opts_.frame_opts.samp_freq);
      float lowpass_cutoff = 0.99 * 0.5 * min_freq;

      int32_t lowpass_filter_width = 6;
      resampler_ = std::make_unique<LinearResample>(
          sampling_rate, opts_.frame_opts.samp_freq, lowpass_cutoff,
          lowpass_filter_width);

      std::vector<float> samples;
      resampler_->Resample(waveform, n, false, &samples);
      fbank_->AcceptWaveform(opts_.frame_opts.samp_freq, samples.data(),
                             samples.size());
      return;
    }

    fbank_->AcceptWaveform(sampling_rate, waveform, n);
  }

  void InputFinished() const {
    std::lock_guard<std::mutex> lock(mutex_);
    fbank_->InputFinished();
  }

  int32_t NumFramesReady() const {
    std::lock_guard<std::mutex> lock(mutex_);
    return fbank_->NumFramesReady();
  }

  bool IsLastFrame(int32_t frame) const {
    std::lock_guard<std::mutex> lock(mutex_);
    return fbank_->IsLastFrame(frame);
  }

  std::vector<float> GetFrames(int32_t frame_index, int32_t n) {
    std::lock_guard<std::mutex> lock(mutex_);
    if (frame_index + n > fbank_->NumFramesReady()) {
      SHERPA_ONNX_LOGE("%d + %d > %d\n", frame_index, n,
                       fbank_->NumFramesReady());
      exit(-1);
    }

    int32_t discard_num = frame_index - last_frame_index_;
    if (discard_num < 0) {
      SHERPA_ONNX_LOGE("last_frame_index_: %d, frame_index_: %d",
                       last_frame_index_, frame_index);
      exit(-1);
    }
    fbank_->Pop(discard_num);

    int32_t feature_dim = fbank_->Dim();
    std::vector<float> features(feature_dim * n);

    float *p = features.data();

    for (int32_t i = 0; i != n; ++i) {
      const float *f = fbank_->GetFrame(i + frame_index);

//      std::cout << "Frame " << i;
//      for (int j = 0; j < feature_dim; j++) {
//          std::cout << " " << f[j];
//      }
//      std::cout << std::endl;

      std::copy(f, f + feature_dim, p);
      p += feature_dim;
    }

    last_frame_index_ = frame_index;

    return features;
  }

  int32_t FeatureDim() const { return opts_.mel_opts.num_bins; }

 private:
  std::unique_ptr<knf::OnlineFbank> fbank_;
  knf::FbankOptions opts_;
  FeatureExtractorConfig config_;
  mutable std::mutex mutex_;
  std::unique_ptr<LinearResample> resampler_;
  int32_t last_frame_index_ = 0;
};

FeatureExtractor::FeatureExtractor(const FeatureExtractorConfig &config /*={}*/)
    : impl_(std::make_unique<Impl>(config)) {}

FeatureExtractor::~FeatureExtractor() = default;

void FeatureExtractor::AcceptWaveform(int32_t sampling_rate,
                                      const float *waveform, int32_t n) const {
  impl_->AcceptWaveform(sampling_rate, waveform, n);
}

void FeatureExtractor::InputFinished() const { impl_->InputFinished(); }

int32_t FeatureExtractor::NumFramesReady() const {
  return impl_->NumFramesReady();
}

bool FeatureExtractor::IsLastFrame(int32_t frame) const {
  return impl_->IsLastFrame(frame);
}

std::vector<float> FeatureExtractor::GetFrames(int32_t frame_index,
                                               int32_t n) const {
  return impl_->GetFrames(frame_index, n);
}

int32_t FeatureExtractor::FeatureDim() const { return impl_->FeatureDim(); }

}  // namespace sherpa_onnx
