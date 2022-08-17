#!/usr/bin/env bash

. ./cmd.sh
. ./path.sh

stage=-1
stop_stage=100

. utils/parse_options.sh

# Data preparation
if [ ${stage} -le 0 ] && [ ${stop_stage} -ge 0 ]; then
  data_url=www.openslr.org/resources/31
  lm_url=www.openslr.org/resources/11
  database=corpus

  mkdir -p $database
  for part in dev-clean-2 train-clean-5; do
    local/download_and_untar.sh $database $data_url $part
  done

  local/download_lm.sh $lm_url $database data/local/lm

  local/data_prep.sh $database/LibriSpeech/train-clean-5 data/train
  local/data_prep.sh $database/LibriSpeech/dev-clean-2 data/test
fi

# Dictionary formatting
if [ ${stage} -le 1 ] && [ ${stop_stage} -ge 1 ]; then
  local/prepare_dict.sh data/local/lm data/local/dict
  utils/prepare_lang.sh data/local/dict "<UNK>" data/local/lang data/lang
fi

# Extract MFCC features
if [ ${stage} -le 2 ] && [ ${stop_stage} -ge 2 ]; then
  for task in train; do
    steps/make_mfcc.sh --cmd "$train_cmd" --nj 10 data/$task exp/make_mfcc/$task $mfcc
    steps/compute_cmvn_stats.sh data/$task exp/make_mfcc/$task $mfcc
  done
fi

# Train GMM models
if [ ${stage} -le 3 ] && [ ${stop_stage} -ge 3 ]; then
  steps/train_mono.sh --nj 10 --cmd "$train_cmd" \
    data/train data/lang exp/mono

  steps/align_si.sh  --nj 10 --cmd "$train_cmd" \
    data/train data/lang exp/mono exp/mono_ali

  steps/train_lda_mllt.sh  --cmd "$train_cmd" \
    2000 10000 data/train data/lang exp/mono_ali exp/tri1

  steps/align_si.sh --nj 10 --cmd "$train_cmd" \
    data/train data/lang exp/tri1 exp/tri1_ali

  steps/train_lda_mllt.sh --cmd "$train_cmd" \
    2500 15000 data/train data/lang exp/tri1_ali exp/tri2

  steps/align_si.sh  --nj 10 --cmd "$train_cmd" \
    data/train data/lang exp/tri2 exp/tri2_ali

  steps/train_lda_mllt.sh --cmd "$train_cmd" \
    2500 20000 data/train data/lang exp/tri2_ali exp/tri3

  steps/align_si.sh  --nj 10 --cmd "$train_cmd" \
    data/train data/lang exp/tri3 exp/tri3_ali
fi

# Train TDNN model
if [ ${stage} -le 4 ] && [ ${stop_stage} -ge 4 ]; then
  local/chain/run_tdnn.sh
fi

# Decode
if [ ${stage} -le 5 ] && [ ${stop_stage} -ge 5 ]; then

  utils/format_lm.sh data/lang data/local/lm/lm_tgsmall.arpa.gz data/local/dict/lexicon.txt data/lang_test
  utils/mkgraph.sh --self-loop-scale 1.0 data/lang_test exp/chain/tdnn exp/chain/tdnn/graph
  utils/build_const_arpa_lm.sh data/local/lm/lm_tgmed.arpa.gz \
    data/lang data/lang_test_rescore

  for task in test; do

    steps/make_mfcc.sh --cmd "$train_cmd" --nj 10 data/$task exp/make_mfcc/$task $mfcc
    steps/compute_cmvn_stats.sh data/$task exp/make_mfcc/$task $mfcc

    steps/online/nnet2/extract_ivectors_online.sh --nj 10 \
        data/${task} exp/chain/extractor \
        exp/chain/ivectors_${task}

    steps/nnet3/decode.sh --cmd $decode_cmd --num-threads 10 --nj 1 \
         --beam 13.0 --max-active 7000 --lattice-beam 4.0 \
         --online-ivector-dir exp/chain/ivectors_${task} \
         --acwt 1.0 --post-decode-acwt 10.0 \
         exp/chain/tdnn/graph data/${task} exp/chain/tdnn/decode_${task}

    steps/lmrescore_const_arpa.sh data/lang_test data/lang_test_rescore \
        data/${task} exp/chain/tdnn/decode_${task} exp/chain/tdnn/decode_${task}_rescore
  done

  bash RESULTS
fi
