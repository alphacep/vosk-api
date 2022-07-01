// Copyright 2019 Alpha Cephei Inc.
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

#ifndef VOSK_BATCH_RECOGNIZER_H
#define VOSK_BATCH_RECOGNIZER_H

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "feat/resample.h"

#include <queue>

#include "batch_model.h"

using namespace kaldi;

class BatchRecognizer {
    public:
        BatchRecognizer(BatchModel *model, float sample_frequency);
        ~BatchRecognizer();

        void AcceptWaveform(const char *data, int len);
        int GetNumPendingChunks();
        const char *FrontResult();
        void Pop();
        void FinishStream();
        void SetNLSML(bool nlsml);

    private:

        void PushLattice(CompactLattice &clat, BaseFloat offset);

        BatchModel *model_;
        uint64_t id_;
        bool initialized_;
        bool callbacks_set_;
        bool nlsml_;
        float sample_frequency_;
        std::queue<std::string> results_;
        LinearResample *resampler_;
        kaldi::Vector<BaseFloat> buffer_;
};

#endif /* VOSK_BATCH_RECOGNIZER_H */
