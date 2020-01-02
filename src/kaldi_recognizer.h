#include "base/kaldi-common.h"
#include "util/common-utils.h"
#include "fstext/fstext-lib.h"
#include "fstext/fstext-utils.h"
#include "decoder/lattice-faster-decoder.h"
#include "feat/feature-mfcc.h"
#include "lat/kaldi-lattice.h"
#include "lat/word-align-lattice.h"
#include "nnet3/am-nnet-simple.h"
#include "nnet3/nnet-am-decodable-simple.h"
#include "nnet3/nnet-utils.h"

#include "model.h"

using namespace kaldi;

class KaldiRecognizer {
    public:
        KaldiRecognizer(Model &model, float sample_frequency);
        ~KaldiRecognizer();
        bool AcceptWaveform(const char *data, int len);
        bool AcceptWaveform(const short *sdata, int len);
        bool AcceptWaveform(const float *fdata, int len);
        std::string Result();
        std::string FinalResult();
        std::string PartialResult();

    private:
        void CleanUp();
        void UpdateSilenceWeights();
        bool AcceptWaveform(Vector<BaseFloat> &wdata);

        Model &model_;
        SingleUtteranceNnet3Decoder *decoder_;
        fst::LookaheadFst<fst::StdArc, int32> *decode_fst_;
        OnlineNnet2FeaturePipeline *feature_pipeline_;
        OnlineSilenceWeighting *silence_weighting_;

        float sample_frequency_;
        int32 frame_offset_;
        bool input_finalized_;
};
