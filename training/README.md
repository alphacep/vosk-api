# Vosk API Training

This directory contains scripts and tools for training speech recognition models using the Kaldi toolkit.

## Table of Contents

1. [Overview](#overview)
2. [Directory Structure](#directory-structure)
3. [Installation](#installation)
4. [Training Process](#training-process)
    - [Data Preparation](#data-preparation)
    - [Dictionary Preparation](#dictionary-preparation)
    - [MFCC Feature Extraction](#mfcc-feature-extraction)
    - [Acoustic Model Training](#acoustic-model-training)
    - [TDNN Chain Model Training](#tdnn-chain-model-training)
    - [Decoding](#decoding)
5. [Results](#results)
6. [Contributing](#contributing)

## Overview

This repository provides tools for training custom speech recognition models using Kaldi. It supports acoustic model training, language model creation, and decoding pipelines.

## Directory Structure

```plaintext
.
├── cmd.sh                         # Command configuration for training and decoding
├── conf/
│   ├── mfcc.conf                  # Configuration for MFCC feature extraction
│   └── online_cmvn.conf           # Online Cepstral Mean Variance Normalization (currently empty)
├── local/
│   ├── chain/
│   │   ├── run_ivector_common.sh  # Script for i-vector extraction during chain model training
│   │   └── run_tdnn.sh            # Script for training a TDNN model
│   ├── data_prep.sh               # Data preparation script for creating Kaldi data directories
│   ├── download_and_untar.sh      # Script for downloading and extracting datasets
│   ├── download_lm.sh             # Downloads language models
│   ├── prepare_dict.sh            # Prepares the pronunciation dictionary
│   └── score.sh                   # Scoring script for evaluation
├── path.sh                        # Script for setting Kaldi paths
├── RESULTS                        # Script for printing the best WER results
├── RESULTS.txt                    # Contains WER results from decoding
├── run.sh                         # Main script for the entire training pipeline
├── steps -> ../../wsj/s5/steps/   # Link to Kaldi’s WSJ steps for acoustic model training
└── utils -> ../../wsj/s5/utils/   # Link to Kaldi’s utility scripts
```

### Key Files:
- **cmd.sh**: Defines commands for running training and decoding tasks.
- **path.sh**: Sets up paths for Kaldi binaries and scripts.
- **run.sh**: Main entry point for the training pipeline, running tasks in stages.
- **RESULTS**: Displays Word Error Rate (WER) for the trained models.

## Installation

### Prerequisites
- [Kaldi](https://github.com/kaldi-asr/kaldi): Kaldi toolkit must be installed and configured.
- Required tools: `ffmpeg`, `sox`, `sctk` for data preparation and scoring.

### Steps
1. Clone the Vosk API repository.
2. Install Kaldi and ensure the `KALDI_ROOT` is correctly set in `path.sh`.
3. Set environment variables using `cmd.sh` and `path.sh`.

## Training Process

### Data Preparation
Run the data preparation stage in `run.sh`:
```bash
bash run.sh --stage 0 --stop_stage 0
```
This stage downloads and prepares the LibriSpeech dataset.

### Dictionary Preparation
Prepare the pronunciation dictionary with:
```bash
bash run.sh --stage 1 --stop_stage 1
```
This step generates the necessary files for Kaldi's `prepare_lang.sh` script.

### MFCC Feature Extraction
Run the MFCC extraction process:
```bash
bash run.sh --stage 2 --stop_stage 2
```
This step extracts Mel-frequency cepstral coefficients (MFCC) features and computes Cepstral Mean Variance Normalization (CMVN).

### Acoustic Model Training
Train monophone, LDA+MLLT, and SAT models:
```bash
bash run.sh --stage 3 --stop_stage 3
```
This stage trains GMM-based models and aligns the data for TDNN training.

### TDNN Chain Model Training
Train a Time-Delay Neural Network (TDNN) chain model:
```bash
bash run.sh --stage 4 --stop_stage 4
```
The chain model uses i-vectors for speaker adaptation.

### Decoding
After training, decode the test data:
```bash
bash run.sh --stage 5 --stop_stage 5
```
This step decodes using the trained model and evaluates the Word Error Rate (WER).

## Results

WER can be evaluated by running:
```bash
bash RESULTS
```
Example of `RESULTS.txt`:
```plaintext
%WER 14.10 [ 2839 / 20138, 214 ins, 487 del, 2138 sub ] exp/chain/tdnn/decode_test/wer_11_0.0
%WER 12.67 [ 2552 / 20138, 215 ins, 406 del, 1931 sub ] exp/chain/tdnn/decode_test_rescore/wer_11_0.0
```