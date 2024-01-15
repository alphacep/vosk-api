// sherpa-onnx/csrc/session.h
//
// Copyright (c)  2023  Xiaomi Corporation

#ifndef SHERPA_ONNX_CSRC_SESSION_H_
#define SHERPA_ONNX_CSRC_SESSION_H_

#include "onnxruntime_cxx_api.h"  // NOLINT
#include "offline-lm-config.h"
#include "offline-model-config.h"
#include "vad-model-config.h"

namespace sherpa_onnx {

Ort::SessionOptions GetSessionOptions(const OfflineModelConfig &config);

Ort::SessionOptions GetSessionOptions(const OfflineLMConfig &config);

Ort::SessionOptions GetSessionOptions(const VadModelConfig &config);

}  // namespace sherpa_onnx

#endif  // SHERPA_ONNX_CSRC_SESSION_H_
