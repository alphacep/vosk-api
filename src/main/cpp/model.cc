#include "model.h"

#include <android/log.h>
static void AndroidLogHandler(const LogMessageEnvelope &env, const char *message)
{
    __android_log_print(ANDROID_LOG_VERBOSE, "KaldiDemo", message, 1);
}

Model::Model() {

    const char *usage = "Read the docs";
    const char *extra_args[] = {
        "--feature-type=mfcc",
        "--mfcc-config=model/mfcc.conf",
        "--min-active=200",
        "--max-active=6000",
        "--beam=13.0",
        "--lattice-beam=6.0",
        "--acoustic-scale=1.0",
        "--frame-subsampling-factor=3",

        "--endpoint.silence-phones=1:2:3:4:5:6:7:8:9:10",
        "--endpoint.rule2.min-trailing-silence=0.5",
        "--endpoint.rule3.min-trailing-silence=1.0",
        "--endpoint.rule4.min-trailing-silence=2.0",


        "--ivector-silence-weighting.silence-weight=0.001",
        "--ivector-silence-weighting.silence-phones=1:2:3:4:5:6:7:8:9:10",
        "--ivector-extraction-config=model/ivector/ivector.conf",
    };

    SetLogHandler(AndroidLogHandler);

    kaldi::ParseOptions po(usage);
    feature_config_.Register(&po);
    nnet3_decoding_config_.Register(&po);
    endpoint_config_.Register(&po);
    decodable_opts_.Register(&po);

    MfccOptions mfcc_opts;
    ReadConfigFromFile("model/mfcc.conf", &mfcc_opts);
    sample_frequency = mfcc_opts.frame_opts.samp_freq;
    KALDI_LOG << "Sample rate is " << sample_frequency;

    std::vector<const char*> args;
    args.push_back("server");
    args.insert(args.end(), extra_args, extra_args + sizeof(extra_args) / sizeof(extra_args[0]));
    po.Read(args.size(), args.data());

    nnet3_rxfilename_ = "model/final.mdl";
    word_syms_rxfilename_ = "model/words.txt";
    fst_rxfilename_ = "model/HCLG.fst";

    trans_model_ = new kaldi::TransitionModel();
    nnet_ = new kaldi::nnet3::AmNnetSimple();
    {
        bool binary;
        kaldi::Input ki(nnet3_rxfilename_, &binary);
        trans_model_->Read(ki.Stream(), binary);
        nnet_->Read(ki.Stream(), binary);
        SetBatchnormTestMode(true, &(nnet_->GetNnet()));
        SetDropoutTestMode(true, &(nnet_->GetNnet()));
        nnet3::CollapseModel(nnet3::CollapseModelConfig(), &(nnet_->GetNnet()));
    }

    decodable_info_ = new nnet3::DecodableNnetSimpleLoopedInfo(decodable_opts_,
                                                               nnet_);
    decode_fst_ = fst::ReadFstKaldiGeneric(fst_rxfilename_);

    word_syms_ = NULL;
    if (!(word_syms_ = fst::SymbolTable::ReadText(word_syms_rxfilename_)))
        KALDI_ERR << "Could not read symbol table from file " << word_syms_rxfilename_;

    kaldi::WordBoundaryInfoNewOpts opts;
    winfo_ = new kaldi::WordBoundaryInfo(opts, "model/word_boundary.int");
}

Model::~Model() {
    delete decodable_info_;
    delete decode_fst_;
    delete trans_model_;
    delete nnet_;
    delete word_syms_;
    delete winfo_;
}
