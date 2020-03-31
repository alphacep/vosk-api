#include "gpu.h"
#include "cudamatrix/cu-device.h"

void Gpu::Init() {
    kaldi::CuDevice::Instantiate().SelectGpuId("yes");
    kaldi::CuDevice::Instantiate().AllowMultithreading();
}

void Gpu::Instantiate() {
    kaldi::CuDevice::Instantiate();
}
