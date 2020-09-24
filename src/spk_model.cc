// Copyright 2020 Alpha Cephei Inc.
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

#include "spk_model.h"

SpkModel::SpkModel(const char *speaker_path) {
    std::string speaker_path_str(speaker_path);

    ReadConfigFromFile(speaker_path_str + "/mfcc.conf", &spkvector_mfcc_opts);
    spkvector_mfcc_opts.frame_opts.allow_downsample = true; // It is safe to downsample

    ReadKaldiObject(speaker_path_str + "/final.ext.raw", &speaker_nnet);
    SetBatchnormTestMode(true, &speaker_nnet);
    SetDropoutTestMode(true, &speaker_nnet);
    CollapseModel(nnet3::CollapseModelConfig(), &speaker_nnet);

    ReadKaldiObject(speaker_path_str + "/mean.vec", &mean);
    ReadKaldiObject(speaker_path_str + "/transform.mat", &transform);

    ref_cnt_ = 1;
}

void SpkModel::Ref() 
{
    ref_cnt_++;
}

void SpkModel::Unref() 
{
    ref_cnt_--;
    if (ref_cnt_ == 0) {
        delete this;
    }
}
