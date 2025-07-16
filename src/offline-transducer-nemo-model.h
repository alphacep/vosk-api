// sherpa-onnx/csrc/offline-transducer-nemo-model.h
//
// Copyright (c)  2024  Xiaomi Corporation
#ifndef SHERPA_ONNX_CSRC_OFFLINE_TRANSDUCER_NEMO_MODEL_H_
#define SHERPA_ONNX_CSRC_OFFLINE_TRANSDUCER_NEMO_MODEL_H_

#include <memory>
#include <string>
#include <utility>
#include <vector>

#include "onnxruntime_cxx_api.h"  // NOLINT
#include "offline-model-config.h"

namespace sherpa_onnx {

// see
// https://github.com/NVIDIA/NeMo/blob/main/nemo/collections/asr/models/hybrid_rnnt_ctc_bpe_models.py#L40
// Its decoder is stateful, not stateless.
class OfflineTransducerNeMoModel {
 public:
  explicit OfflineTransducerNeMoModel(const OfflineModelConfig &config);

  template <typename Manager>
  OfflineTransducerNeMoModel(Manager *mgr, const OfflineModelConfig &config);

  ~OfflineTransducerNeMoModel();

  /** Run the encoder.
   *
   * @param features  A tensor of shape (N, T, C). It is changed in-place.
   * @param features_length  A 1-D tensor of shape (N,) containing number of
   *                         valid frames in `features` before padding.
   *                         Its dtype is int64_t.
   *
   * @return Return a vector containing:
   *  - encoder_out: A 3-D tensor of shape (N, T', encoder_dim)
   *  - encoder_out_length: A 1-D tensor of shape (N,) containing number
   *                        of frames in `encoder_out` before padding.
   */
  std::vector<Ort::Value> RunEncoder(Ort::Value features,
                                     Ort::Value features_length) const;

  /** Run the decoder network.
   *
   * @param targets A int32 tensor of shape (batch_size, 1)
   * @param targets_length A int32 tensor of shape (batch_size,)
   * @param states The states for the decoder model.
   * @return Return a vector:
   *           - ans[0] is the decoder_out (a float tensor)
   *           - ans[1] is the decoder_out_length (a int32 tensor)
   *           - ans[2:] is the states_next
   */
  std::pair<Ort::Value, std::vector<Ort::Value>> RunDecoder(
      Ort::Value targets, Ort::Value targets_length,
      std::vector<Ort::Value> states) const;

  std::vector<Ort::Value> GetDecoderInitStates(int32_t batch_size) const;

  /** Run the joint network.
   *
   * @param encoder_out Output of the encoder network.
   * @param decoder_out Output of the decoder network.
   * @return Return a tensor of shape (N, 1, 1, vocab_size) containing logits.
   */
  Ort::Value RunJoiner(Ort::Value encoder_out, Ort::Value decoder_out) const;

  /** Return the subsampling factor of the model.
   */
  int32_t SubsamplingFactor() const;

  int32_t VocabSize() const;

  /** Return an allocator for allocating memory
   */
  OrtAllocator *Allocator() const;

  // Possible values:
  // - per_feature
  // - all_features (not implemented yet)
  // - fixed_mean (not implemented)
  // - fixed_std (not implemented)
  // - or just leave it to empty
  // See
  // https://github.com/NVIDIA/NeMo/blob/main/nemo/collections/asr/parts/preprocessing/features.py#L59
  // for details
  std::string FeatureNormalizationMethod() const;

  bool IsGigaAM() const;

  int32_t FeatureDim() const;

 private:
  class Impl;
  std::unique_ptr<Impl> impl_;
};

}  // namespace sherpa_onnx

#endif  // SHERPA_ONNX_CSRC_OFFLINE_TRANSDUCER_NEMO_MODEL_H_
