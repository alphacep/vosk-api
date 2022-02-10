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

#ifndef VOSK_GPU_RECOGNIZER_H
#define VOSK_GPU_RECOGNIZER_H

#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "fstext/fstext-lib.h"
#include "fstext/fstext-utils.h"
#include "decoder/lattice-faster-decoder.h"
#include "feat/feature-mfcc.h"
#include "lat/kaldi-lattice.h"
#include "lat/word-align-lattice.h"
#include "lat/compose-lattice-pruned.h"
#include "nnet3/am-nnet-simple.h"
#include "nnet3/nnet-am-decodable-simple.h"
#include "nnet3/nnet-utils.h"

#include "cudadecoder/cuda-online-pipeline-dynamic-batcher.h"
#include "cudadecoder/batched-threaded-nnet3-cuda-online-pipeline.h"
#include "cudadecoder/batched-threaded-nnet3-cuda-pipeline2.h"
#include "cudadecoder/cuda-pipeline-common.h"

#include "model.h"

using namespace kaldi;
using namespace kaldi::cuda_decoder;

class BatchRecognizer {
    public:
        BatchRecognizer();
        ~BatchRecognizer();

        void FinishStream(uint64_t id);
        void AcceptWaveform(uint64_t id, const char *data, int len);
        const char *FrontResult(uint64_t id);
        void Pop(uint64_t id);
        void WaitForCompletion();
        int GetNumPendingChunks(uint64_t id);

    private:
        struct Stream {
            bool initialized = false;
            std::queue<std::string> results;
            kaldi::Vector<BaseFloat> buffer;
        };

        void PushLattice(uint64_t id, CompactLattice &clat, BaseFloat offset);

        kaldi::TransitionModel *trans_model_ = nullptr;
        kaldi::nnet3::AmNnetSimple *nnet_ = nullptr;
        const fst::SymbolTable *word_syms_ = nullptr;

        fst::Fst<fst::StdArc> *hclg_fst_ = nullptr;
        kaldi::WordBoundaryInfo *winfo_ = nullptr;

        fst::VectorFst<fst::StdArc> *graph_lm_fst_ = nullptr;
        kaldi::ConstArpaLm const_arpa_;

        BatchedThreadedNnet3CudaOnlinePipeline *cuda_pipeline_ = nullptr;
        CudaOnlinePipelineDynamicBatcher *dynamic_batcher_ = nullptr;

        int32 samples_per_chunk_;

        // Input and output queues
        std::map<int, Stream> streams_;

        // Rescoring
        fst::ArcMapFst<fst::StdArc, LatticeArc, fst::StdToLatticeMapper<BaseFloat> > *lm_to_subtract_ = nullptr;
        kaldi::ConstArpaLmDeterministicFst *carpa_to_add_ = nullptr;
        fst::ScaleDeterministicOnDemandFst *carpa_to_add_scale_ = nullptr;

        float sample_frequency_;
};

#endif /* VOSK_GPU_RECOGNIZER_H */
