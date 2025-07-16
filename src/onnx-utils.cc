// onnx-utils.cc
//
// Copyright (c)  2023  Xiaomi Corporation
// Copyright (c)  2023  Pingfeng Luo
#include "onnx-utils.h"

#include <algorithm>
#include <fstream>
#include <sstream>
#include <string>

#if __ANDROID_API__ >= 9
#include "android/asset_manager.h"
#include "android/asset_manager_jni.h"
#include "android/log.h"
#endif

#include "onnxruntime_cxx_api.h"  // NOLINT

namespace sherpa_onnx {

void GetInputNames(Ort::Session *sess, std::vector<std::string> *input_names,
                   std::vector<const char *> *input_names_ptr) {
  Ort::AllocatorWithDefaultOptions allocator;
  size_t node_count = sess->GetInputCount();
  input_names->resize(node_count);
  input_names_ptr->resize(node_count);
  for (size_t i = 0; i != node_count; ++i) {
    auto tmp = sess->GetInputNameAllocated(i, allocator);
    (*input_names)[i] = tmp.get();
    (*input_names_ptr)[i] = (*input_names)[i].c_str();
  }
}

void GetOutputNames(Ort::Session *sess, std::vector<std::string> *output_names,
                    std::vector<const char *> *output_names_ptr) {
  Ort::AllocatorWithDefaultOptions allocator;
  size_t node_count = sess->GetOutputCount();
  output_names->resize(node_count);
  output_names_ptr->resize(node_count);
  for (size_t i = 0; i != node_count; ++i) {
    auto tmp = sess->GetOutputNameAllocated(i, allocator);
    (*output_names)[i] = tmp.get();
    (*output_names_ptr)[i] = (*output_names)[i].c_str();
  }
}

Ort::Value GetEncoderOutFrame(OrtAllocator *allocator, Ort::Value *encoder_out,
                              int32_t t) {
  std::vector<int64_t> encoder_out_shape =
      encoder_out->GetTensorTypeAndShapeInfo().GetShape();

  auto batch_size = encoder_out_shape[0];
  auto num_frames = encoder_out_shape[1];
  assert(t < num_frames);

  auto encoder_out_dim = encoder_out_shape[2];

  auto offset = num_frames * encoder_out_dim;

  std::array<int64_t, 2> shape{batch_size, encoder_out_dim};

  Ort::Value ans =
      Ort::Value::CreateTensor<float>(allocator, shape.data(), shape.size());

  float *dst = ans.GetTensorMutableData<float>();
  const float *src = encoder_out->GetTensorData<float>();

  for (int32_t i = 0; i != batch_size; ++i) {
    std::copy(src + t * encoder_out_dim, src + (t + 1) * encoder_out_dim, dst);
    src += offset;
    dst += encoder_out_dim;
  }
  return ans;
}

void PrintModelMetadata(std::ostream &os, const Ort::ModelMetadata &meta_data) {
  Ort::AllocatorWithDefaultOptions allocator;
  std::vector<Ort::AllocatedStringPtr> v =
      meta_data.GetCustomMetadataMapKeysAllocated(allocator);
  for (const auto &key : v) {
    auto p = meta_data.LookupCustomMetadataMapAllocated(key.get(), allocator);
    os << key.get() << "=" << p.get() << "\n";
  }
}

Ort::Value Clone(OrtAllocator *allocator, const Ort::Value *v) {
  auto type_and_shape = v->GetTensorTypeAndShapeInfo();
  std::vector<int64_t> shape = type_and_shape.GetShape();

  switch (type_and_shape.GetElementType()) {
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT32: {
      Ort::Value ans = Ort::Value::CreateTensor<int32_t>(
          allocator, shape.data(), shape.size());
      const int32_t *start = v->GetTensorData<int32_t>();
      const int32_t *end = start + type_and_shape.GetElementCount();
      int32_t *dst = ans.GetTensorMutableData<int32_t>();
      std::copy(start, end, dst);
      return ans;
    }
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64: {
      Ort::Value ans = Ort::Value::CreateTensor<int64_t>(
          allocator, shape.data(), shape.size());
      const int64_t *start = v->GetTensorData<int64_t>();
      const int64_t *end = start + type_and_shape.GetElementCount();
      int64_t *dst = ans.GetTensorMutableData<int64_t>();
      std::copy(start, end, dst);
      return ans;
    }
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT: {
      Ort::Value ans = Ort::Value::CreateTensor<float>(allocator, shape.data(),
                                                       shape.size());
      const float *start = v->GetTensorData<float>();
      const float *end = start + type_and_shape.GetElementCount();
      float *dst = ans.GetTensorMutableData<float>();
      std::copy(start, end, dst);
      return ans;
    }
    default:
      fprintf(stderr, "Unsupported type: %d\n",
              static_cast<int32_t>(type_and_shape.GetElementType()));
      exit(-1);
      // unreachable code
      return Ort::Value{nullptr};
  }
}

Ort::Value View(Ort::Value *v) {
  auto type_and_shape = v->GetTensorTypeAndShapeInfo();
  std::vector<int64_t> shape = type_and_shape.GetShape();

  auto memory_info =
      Ort::MemoryInfo::CreateCpu(OrtDeviceAllocator, OrtMemTypeDefault);
  switch (type_and_shape.GetElementType()) {
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT32:
      return Ort::Value::CreateTensor(
          memory_info, v->GetTensorMutableData<int32_t>(),
          type_and_shape.GetElementCount(), shape.data(), shape.size());
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_INT64:
      return Ort::Value::CreateTensor(
          memory_info, v->GetTensorMutableData<int64_t>(),
          type_and_shape.GetElementCount(), shape.data(), shape.size());
    case ONNX_TENSOR_ELEMENT_DATA_TYPE_FLOAT:
      return Ort::Value::CreateTensor(
          memory_info, v->GetTensorMutableData<float>(),
          type_and_shape.GetElementCount(), shape.data(), shape.size());
    default:
      fprintf(stderr, "Unsupported type: %d\n",
              static_cast<int32_t>(type_and_shape.GetElementType()));
      exit(-1);
      // unreachable code
      return Ort::Value{nullptr};
  }
}

void Print1D(Ort::Value *v) {
  std::vector<int64_t> shape = v->GetTensorTypeAndShapeInfo().GetShape();
  const float *d = v->GetTensorData<float>();
  for (int32_t i = 0; i != static_cast<int32_t>(shape[0]); ++i) {
    fprintf(stderr, "%.3f ", d[i]);
  }
  fprintf(stderr, "\n");
}

template <typename T /*= float*/>
void Print2D(Ort::Value *v) {
  std::vector<int64_t> shape = v->GetTensorTypeAndShapeInfo().GetShape();
  const T *d = v->GetTensorData<T>();

  std::ostringstream os;
  for (int32_t r = 0; r != static_cast<int32_t>(shape[0]); ++r) {
    for (int32_t c = 0; c != static_cast<int32_t>(shape[1]); ++c, ++d) {
      os << *d << " ";
    }
    os << "\n";
  }
  fprintf(stderr, "%s\n", os.str().c_str());
}

template void Print2D<int64_t>(Ort::Value *v);
template void Print2D<float>(Ort::Value *v);

void Print3D(Ort::Value *v) {
  std::vector<int64_t> shape = v->GetTensorTypeAndShapeInfo().GetShape();
  const float *d = v->GetTensorData<float>();

  for (int32_t p = 0; p != static_cast<int32_t>(shape[0]); ++p) {
    fprintf(stderr, "---plane %d---\n", p);
    for (int32_t r = 0; r != static_cast<int32_t>(shape[1]); ++r) {
      for (int32_t c = 0; c != static_cast<int32_t>(shape[2]); ++c, ++d) {
        fprintf(stderr, "%.3f ", *d);
      }
      fprintf(stderr, "\n");
    }
  }
  fprintf(stderr, "\n");
}

void Print4D(Ort::Value *v) {
  std::vector<int64_t> shape = v->GetTensorTypeAndShapeInfo().GetShape();
  const float *d = v->GetTensorData<float>();

  for (int32_t p = 0; p != static_cast<int32_t>(shape[0]); ++p) {
    fprintf(stderr, "---plane %d---\n", p);
    for (int32_t q = 0; q != static_cast<int32_t>(shape[1]); ++q) {
      fprintf(stderr, "---subplane %d---\n", q);
      for (int32_t r = 0; r != static_cast<int32_t>(shape[2]); ++r) {
        for (int32_t c = 0; c != static_cast<int32_t>(shape[3]); ++c, ++d) {
          fprintf(stderr, "%.3f ", *d);
        }
        fprintf(stderr, "\n");
      }
      fprintf(stderr, "\n");
    }
  }
  fprintf(stderr, "\n");
}

std::vector<char> ReadFile(const std::string &filename) {
  std::ifstream input(filename, std::ios::binary);
  std::vector<char> buffer(std::istreambuf_iterator<char>(input), {});
  return buffer;
}

#if __ANDROID_API__ >= 9
std::vector<char> ReadFile(AAssetManager *mgr, const std::string &filename) {
  AAsset *asset = AAssetManager_open(mgr, filename.c_str(), AASSET_MODE_BUFFER);
  if (!asset) {
    __android_log_print(ANDROID_LOG_FATAL, "sherpa-onnx",
                        "Read binary file: Load %s failed", filename.c_str());
    exit(-1);
  }

  auto p = reinterpret_cast<const char *>(AAsset_getBuffer(asset));
  size_t asset_length = AAsset_getLength(asset);

  std::vector<char> buffer(p, p + asset_length);
  AAsset_close(asset);

  return buffer;
}
#endif

Ort::Value Repeat(OrtAllocator *allocator, Ort::Value *cur_encoder_out,
                  const std::vector<int32_t> &hyps_num_split) {
  std::vector<int64_t> cur_encoder_out_shape =
      cur_encoder_out->GetTensorTypeAndShapeInfo().GetShape();

  std::array<int64_t, 2> ans_shape{hyps_num_split.back(),
                                   cur_encoder_out_shape[1]};

  Ort::Value ans = Ort::Value::CreateTensor<float>(allocator, ans_shape.data(),
                                                   ans_shape.size());

  const float *src = cur_encoder_out->GetTensorData<float>();
  float *dst = ans.GetTensorMutableData<float>();
  int32_t batch_size = static_cast<int32_t>(hyps_num_split.size()) - 1;
  for (int32_t b = 0; b != batch_size; ++b) {
    int32_t cur_stream_hyps_num = hyps_num_split[b + 1] - hyps_num_split[b];
    for (int32_t i = 0; i != cur_stream_hyps_num; ++i) {
      std::copy(src, src + cur_encoder_out_shape[1], dst);
      dst += cur_encoder_out_shape[1];
    }
    src += cur_encoder_out_shape[1];
  }
  return ans;
}

CopyableOrtValue::CopyableOrtValue(const CopyableOrtValue &other) {
  *this = other;
}

CopyableOrtValue &CopyableOrtValue::operator=(const CopyableOrtValue &other) {
  if (this == &other) {
    return *this;
  }
  if (other.value) {
    Ort::AllocatorWithDefaultOptions allocator;
    value = Clone(allocator, &other.value);
  }
  return *this;
}

CopyableOrtValue::CopyableOrtValue(CopyableOrtValue &&other) {
  *this = std::move(other);
}

CopyableOrtValue &CopyableOrtValue::operator=(CopyableOrtValue &&other) {
  if (this == &other) {
    return *this;
  }
  value = std::move(other.value);
  return *this;
}

std::vector<CopyableOrtValue> Convert(std::vector<Ort::Value> values) {
  std::vector<CopyableOrtValue> ans;
  ans.reserve(values.size());

  for (auto &v : values) {
    ans.emplace_back(std::move(v));
  }

  return ans;
}

std::vector<Ort::Value> Convert(std::vector<CopyableOrtValue> values) {
  std::vector<Ort::Value> ans;
  ans.reserve(values.size());

  for (auto &v : values) {
    ans.emplace_back(std::move(v.value));
  }

  return ans;
}

std::string LookupCustomModelMetaData(const Ort::ModelMetadata &meta_data,
                                      const char *key,
                                      OrtAllocator *allocator) {
// Note(fangjun): We only tested 1.17.1 and 1.11.0
// For other versions, we may need to change it
#if ORT_API_VERSION >= 12
  auto v = meta_data.LookupCustomMetadataMapAllocated(key, allocator);
  return v ? v.get() : "";
#else
  auto v = meta_data.LookupCustomMetadataMap(key, allocator);
  std::string ans = v ? v : "";
  allocator->Free(allocator, v);
  return ans;
#endif
}

}  // namespace sherpa_onnx
