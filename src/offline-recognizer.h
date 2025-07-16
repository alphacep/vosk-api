// offline-recognizer.h
//
// Copyright (c)  2023  Xiaomi Corporation

#ifndef SHERPA_ONNX_CSRC_OFFLINE_RECOGNIZER_H_
#define SHERPA_ONNX_CSRC_OFFLINE_RECOGNIZER_H_

#include <memory>
#include <string>
#include <vector>

#if __ANDROID_API__ >= 9
#include "android/asset_manager.h"
#include "android/asset_manager_jni.h"
#endif

#include "offline-lm-config.h"
#include "offline-model-config.h"
#include "offline-stream.h"
#include "offline-transducer-model-config.h"
#include "parse-options.h"

namespace sherpa_onnx {

struct OfflineRecognitionResult;

struct OfflineRecognizerConfig {
  OfflineFeatureExtractorConfig feat_config;
  OfflineModelConfig model_config;
  OfflineLMConfig lm_config;

  std::string decoding_method = "greedy_search";
  int32_t max_active_paths = 4;

  std::string hotwords_file;
  float hotwords_score = 1.5;

  float blank_penalty = 0.0;

  // only greedy_search is implemented
  // TODO(fangjun): Implement modified_beam_search

  OfflineRecognizerConfig() = default;
  OfflineRecognizerConfig(
      const OfflineFeatureExtractorConfig &feat_config,
      const OfflineModelConfig &model_config, const OfflineLMConfig &lm_config,
      const std::string &decoding_method, int32_t max_active_paths,
      const std::string &hotwords_file, float hotwords_score)
      : feat_config(feat_config),
        model_config(model_config),
        lm_config(lm_config),
        decoding_method(decoding_method),
        max_active_paths(max_active_paths),
        hotwords_file(hotwords_file),
        hotwords_score(hotwords_score) {}

  void Register(ParseOptions *po);
  bool Validate() const;

  std::string ToString() const;
};

class OfflineRecognizerImpl;

class OfflineRecognizer {
 public:
  ~OfflineRecognizer();

#if __ANDROID_API__ >= 9
  OfflineRecognizer(AAssetManager *mgr, const OfflineRecognizerConfig &config);
#endif

  explicit OfflineRecognizer(const OfflineRecognizerConfig &config);

  /// Create a stream for decoding.
  std::unique_ptr<OfflineStream> CreateStream() const;

  /** Create a stream for decoding.
   *
   *  @param The hotwords for this string, it might contain several hotwords,
   *         the hotwords are separated by "/". In each of the hotwords, there
   *         are cjkchars or bpes, the bpe/cjkchar are separated by space (" ").
   *         For example, hotwords I LOVE YOU and HELLO WORLD, looks like:
   *
   *         "▁I ▁LOVE ▁YOU/▁HE LL O ▁WORLD"
   */
  std::unique_ptr<OfflineStream> CreateStream(
      const std::string &hotwords) const;

  /** Decode a single stream
   *
   * @param s The stream to decode.
   */
  void DecodeStream(OfflineStream *s) const {
    OfflineStream *ss[1] = {s};
    DecodeStreams(ss, 1);
  }

  /** Decode a list of streams.
   *
   * @param ss Pointer to an array of streams.
   * @param n  Size of the input array.
   */
  void DecodeStreams(OfflineStream **ss, int32_t n) const;

 private:
  std::unique_ptr<OfflineRecognizerImpl> impl_;
};

}  // namespace sherpa_onnx

#endif  // SHERPA_ONNX_CSRC_OFFLINE_RECOGNIZER_H_
