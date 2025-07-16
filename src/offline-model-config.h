// offline-model-config.h
//
// Copyright (c)  2023  Xiaomi Corporation
#ifndef SHERPA_ONNX_CSRC_OFFLINE_MODEL_CONFIG_H_
#define SHERPA_ONNX_CSRC_OFFLINE_MODEL_CONFIG_H_

#include <string>

#include "offline-transducer-model-config.h"

namespace sherpa_onnx {

struct OfflineModelConfig {
  OfflineTransducerModelConfig transducer;

  std::string tokens;
  int32_t num_threads = 0;
  bool debug = false;
  std::string provider = "cpu";

  // With the help of this field, we only need to load the model once
  // instead of twice; and therefore it reduces initialization time.
  //
  // Valid values:
  //  - transducer. The given model is from icefall
  //  - paraformer. It is a paraformer model
  //  - nemo_ctc. It is a NeMo CTC model.
  //
  // All other values are invalid and lead to loading the model twice.
  std::string model_type;

  OfflineModelConfig() = default;
  OfflineModelConfig(const OfflineTransducerModelConfig &transducer,
                     const std::string &tokens, int32_t num_threads, bool debug,
                     const std::string &provider, const std::string &model_type)
      : transducer(transducer),
        tokens(tokens),
        num_threads(num_threads),
        debug(debug),
        provider(provider),
        model_type(model_type) {}

  void Register(ParseOptions *po);
  bool Validate() const;

  std::string ToString() const;
};

}  // namespace sherpa_onnx

#endif  // SHERPA_ONNX_CSRC_OFFLINE_MODEL_CONFIG_H_
