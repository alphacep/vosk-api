// silero-vad-model.cc
//
// Copyright (c)  2023  Xiaomi Corporation

#include "silero-vad-model.h"

#include <string>
#include <utility>
#include <vector>
#include <iostream>

#include "macros.h"
#include "onnx-utils.h"
#include "session.h"

namespace sherpa_onnx {

class SileroVadModel::Impl {
 public:
  explicit Impl(const VadModelConfig &config)
      : config_(config),
        env_(ORT_LOGGING_LEVEL_ERROR),
        sess_opts_(GetSessionOptions(config)),
        allocator_{} {

    auto buf = ReadFile(config.silero_vad.model);
    Init(buf.data(), buf.size());

    sample_rate_ = config.sample_rate;
    if (sample_rate_ != 16000 && sample_rate_ != 8000) {
      SHERPA_ONNX_LOGE("Expected sample rate 16000 or 8000. Given: %d",
                       config.sample_rate);
      exit(-1);
    }

    min_silence_samples_ =
        sample_rate_ * config_.silero_vad.min_silence_duration;

    min_speech_samples_ = sample_rate_ * config_.silero_vad.min_speech_duration;
    max_samples_ = sample_rate_ * config_.silero_vad.max_duration;
  }

#if __ANDROID_API__ >= 9
  Impl(AAssetManager *mgr, const VadModelConfig &config)
      : config_(config),
        env_(ORT_LOGGING_LEVEL_ERROR),
        sess_opts_(GetSessionOptions(config)),
        allocator_{} {
    auto buf = ReadFile(mgr, config.silero_vad.model);
    Init(buf.data(), buf.size());

    sample_rate_ = config.sample_rate;
    if (sample_rate_ != 16000) {
      SHERPA_ONNX_LOGE("Expected sample rate 16000. Given: %d",
                       config.sample_rate);
      exit(-1);
    }

    min_silence_samples_ =
        sample_rate_ * config_.silero_vad.min_silence_duration;

    min_speech_samples_ = sample_rate_ * config_.silero_vad.min_speech_duration;

    max_samples_ = sample_rate_ * config_.silero_vad.max_duration;
  }
#endif

  void Reset() {
    // 2 - number of LSTM layer
    // 1 - batch size
    // 64 - hidden dim
    std::array<int64_t, 3> shape{2, 1, 64};

    Ort::Value h =
        Ort::Value::CreateTensor<float>(allocator_, shape.data(), shape.size());

    Ort::Value c =
        Ort::Value::CreateTensor<float>(allocator_, shape.data(), shape.size());

    Fill<float>(&h, 0);
    Fill<float>(&c, 0);

    states_.clear();

    states_.reserve(2);
    states_.push_back(std::move(h));
    states_.push_back(std::move(c));

    triggered_ = false;
    silence_repeated_ = false;
    current_sample_ = 0;
    temp_start_ = 0;
    temp_end_ = 0;
  }

  bool IsSpeech(const float *samples, int32_t n) {
    if (n != config_.silero_vad.window_size) {
      SHERPA_ONNX_LOGE("n: %d != window_size: %d", n,
                       config_.silero_vad.window_size);
      exit(-1);
    }

    auto memory_info =
        Ort::MemoryInfo::CreateCpu(OrtDeviceAllocator, OrtMemTypeDefault);

    std::array<int64_t, 2> x_shape = {1, n};

    Ort::Value x =
        Ort::Value::CreateTensor(memory_info, const_cast<float *>(samples), n,
                                 x_shape.data(), x_shape.size());

    int64_t sr_shape = 1;
    Ort::Value sr =
        Ort::Value::CreateTensor(memory_info, &sample_rate_, 1, &sr_shape, 1);

    std::array<Ort::Value, 4> inputs = {std::move(x), std::move(sr),
                                        std::move(states_[0]),
                                        std::move(states_[1])};

    auto out =
        sess_->Run({}, input_names_ptr_.data(), inputs.data(), inputs.size(),
                   output_names_ptr_.data(), output_names_ptr_.size());

    states_[0] = std::move(out[1]);
    states_[1] = std::move(out[2]);

    float prob = out[0].GetTensorData<float>()[0];

    float threshold = config_.silero_vad.threshold;

    current_sample_ += config_.silero_vad.window_size;

//    std::cerr << "Silero " << current_sample_ << " " << current_sample_ / 16000.0 << " " << prob << std::endl;

    if (prob > threshold && temp_end_ != 0) {
      temp_end_ = 0;
    }

    if (prob > threshold && temp_start_ == 0) {
      // start speaking, but we require that it must satisfy
      // min_speech_duration
      temp_start_ = current_sample_;
      silence_repeated_ = false;
      return false;
    }

    if (prob > threshold && temp_start_ != 0 && !triggered_) {
      silence_repeated_ = false;
      if (current_sample_ - temp_start_ < min_speech_samples_) {
        return false;
      }
      triggered_ = true;
      return true;
    }

    // Avoid too long utterances
    if (prob > threshold && temp_start_ != 0 && triggered_) {
      if (current_sample_ - temp_start_ > max_samples_) {
        return false;
      }
    }

    if ((prob < threshold) && !triggered_ && !silence_repeated_) {
      // Don't reset start immediately, wait for the next silence
      silence_repeated_ = true;
      return false;
    }

    if ((prob < threshold) && !triggered_ && silence_repeated_) {
      // silence
      temp_start_ = 0;
      temp_end_ = 0;
      return false;
    }

    if ((prob > threshold) && triggered_) {
      // speaking
      return true;
    }

    if ((prob > threshold) && !triggered_) {
      // start speaking
      triggered_ = true;

      return true;
    }

    if ((prob < threshold) && triggered_) {
      // stop to speak
      if (temp_end_ == 0) {
        temp_end_ = current_sample_;
      }

      if (current_sample_ - temp_end_ < min_silence_samples_) {
        // continue speaking
        return true;
      }
      // stopped speaking
      temp_start_ = 0;
      temp_end_ = 0;
      triggered_ = false;
      silence_repeated_ = false;
      return false;
    }

    return false;
  }

  int32_t WindowSize() const { return config_.silero_vad.window_size; }

  int32_t MinSilenceDurationSamples() const { return min_silence_samples_; }

  int32_t MinSpeechDurationSamples() const { return min_speech_samples_; }

  void SetEndpointerDelays(float t_start_max, float t_end, float t_max) { 
    min_silence_samples_ = sample_rate_ * t_end;
    max_samples_ = sample_rate_ * t_max;
  }

 private:
  void Init(void *model_data, size_t model_data_length) {
    sess_opts_.SetGraphOptimizationLevel(GraphOptimizationLevel::ORT_DISABLE_ALL);

    sess_ = std::make_unique<Ort::Session>(env_, model_data, model_data_length,
                                           sess_opts_);

    GetInputNames(sess_.get(), &input_names_, &input_names_ptr_);
    GetOutputNames(sess_.get(), &output_names_, &output_names_ptr_);
    Check();

    Reset();
  }

  void Check() {
    if (input_names_.size() != 4) {
      SHERPA_ONNX_LOGE("Expect 4 inputs. Given: %d",
                       static_cast<int32_t>(input_names_.size()));
      exit(-1);
    }

    if (input_names_[0] != "input") {
      SHERPA_ONNX_LOGE("Input[0]: %s. Expected: input",
                       input_names_[0].c_str());
      exit(-1);
    }

    if (input_names_[1] != "sr") {
      SHERPA_ONNX_LOGE("Input[1]: %s. Expected: sr", input_names_[1].c_str());
      exit(-1);
    }

    if (input_names_[2] != "h") {
      SHERPA_ONNX_LOGE("Input[2]: %s. Expected: h", input_names_[2].c_str());
      exit(-1);
    }

    if (input_names_[3] != "c") {
      SHERPA_ONNX_LOGE("Input[3]: %s. Expected: c", input_names_[3].c_str());
      exit(-1);
    }

    // Now for outputs
    if (output_names_.size() != 3) {
      SHERPA_ONNX_LOGE("Expect 3 outputs. Given: %d",
                       static_cast<int32_t>(output_names_.size()));
      exit(-1);
    }

    if (output_names_[0] != "output") {
      SHERPA_ONNX_LOGE("Output[0]: %s. Expected: output",
                       output_names_[0].c_str());
      exit(-1);
    }

    if (output_names_[1] != "hn") {
      SHERPA_ONNX_LOGE("Output[1]: %s. Expected: sr", output_names_[1].c_str());
      exit(-1);
    }

    if (output_names_[2] != "cn") {
      SHERPA_ONNX_LOGE("Output[2]: %s. Expected: sr", output_names_[2].c_str());
      exit(-1);
    }
  }

 private:
  VadModelConfig config_;

  Ort::Env env_;
  Ort::SessionOptions sess_opts_;
  Ort::AllocatorWithDefaultOptions allocator_;

  std::unique_ptr<Ort::Session> sess_;

  std::vector<std::string> input_names_;
  std::vector<const char *> input_names_ptr_;

  std::vector<std::string> output_names_;
  std::vector<const char *> output_names_ptr_;

  std::vector<Ort::Value> states_;
  int64_t sample_rate_;
  int32_t min_silence_samples_;
  int32_t min_speech_samples_;
  int32_t max_samples_;

  bool triggered_ = false;
  bool silence_repeated_ = false;
  int32_t current_sample_ = 0;
  int32_t temp_start_ = 0;
  int32_t temp_end_ = 0;
};

SileroVadModel::SileroVadModel(const VadModelConfig &config)
    : impl_(std::make_unique<Impl>(config)) {}

#if __ANDROID_API__ >= 9
SileroVadModel::SileroVadModel(AAssetManager *mgr, const VadModelConfig &config)
    : impl_(std::make_unique<Impl>(mgr, config)) {}
#endif

SileroVadModel::~SileroVadModel() = default;

void SileroVadModel::Reset() { return impl_->Reset(); }

bool SileroVadModel::IsSpeech(const float *samples, int32_t n) {
  return impl_->IsSpeech(samples, n);
}

int32_t SileroVadModel::WindowSize() const { return impl_->WindowSize(); }

int32_t SileroVadModel::MinSilenceDurationSamples() const {
  return impl_->MinSilenceDurationSamples();
}

int32_t SileroVadModel::MinSpeechDurationSamples() const {
  return impl_->MinSpeechDurationSamples();
}

void SileroVadModel::SetEndpointerDelays(float t_start_max, float t_end, float t_max) const {
  impl_->SetEndpointerDelays(t_start_max, t_end, t_max); 
}

}  // namespace sherpa_onnx
