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
    ReadConfigFromFile(speaker_path_str + "/vad.conf", &vad_opts);
    spkvector_mfcc_opts.frame_opts.allow_downsample = true; // It is safe to downsample

    plda_rxfilename = speaker_path_str + "/plda_adapt.smooth0.1"; // smoothed version of PLDA
    ReadKaldiObject(plda_rxfilename, &plda);
    train_ivector_rspecifier = "ark:" + speaker_path_str + "/spk_xvectors.ark"; // train speaker xvectors file
    num_utts_rspecifier = "ark:" + speaker_path_str + "/num_utts.ark";

    RandomAccessInt32Reader num_utts_reader(num_utts_rspecifier);

    double tot_test_renorm_scale = 0.0, tot_train_renorm_scale = 0.0;
    int64 num_train_ivectors = 0, num_train_errs = 0, num_test_ivectors = 0;
    int32 dim = plda.Dim();
    SequentialBaseFloatVectorReader train_ivector_reader(train_ivector_rspecifier);
    for (; !train_ivector_reader.Done(); train_ivector_reader.Next()) { // reading train xvectors
        std::string spk = train_ivector_reader.Key();
        if (train_ivectors.count(spk) != 0) {
            KALDI_ERR << "Duplicate training iVector found for speaker " << spk;
        }
        const Vector<BaseFloat> &ivector = train_ivector_reader.Value();
        int32 num_examples;
        if (!num_utts_rspecifier.empty()) {
            if (!num_utts_reader.HasKey(spk)) {
                KALDI_WARN << "Number of utterances not given for speaker " << spk;
                num_train_errs++;
                continue;
            }
            num_examples = num_utts_reader.Value(spk);
        } else {
            num_examples = 1;
        }
        num_utts.insert(std::pair<std::string, int32>(spk, num_examples));

        //  Transformed version of xvectors
        Vector<BaseFloat> *transformed_ivector = new Vector<BaseFloat>(dim);
        tot_train_renorm_scale += plda.TransformIvector(plda_config, ivector,
                                                        num_examples,
                                                        transformed_ivector);
        train_ivectors[spk] = transformed_ivector;
        num_train_ivectors++;
    }

    KALDI_LOG << "Read " << num_train_ivectors << " training iVectors, "
              << "errors on " << num_train_errs;
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
    std::atomic_fetch_add_explicit(&ref_cnt_, 1, std::memory_order_relaxed);
}

void SpkModel::Unref()
{
    if (std::atomic_fetch_sub_explicit(&ref_cnt_, 1, std::memory_order_release) == 1) {
         std::atomic_thread_fence(std::memory_order_acquire);
         delete this;
    }
}
