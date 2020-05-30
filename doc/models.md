# Models

This is the list of models compatible with Vosk-API.

To add a new model here create an issue on Github.

| Model                                                                                                     | Size  | Accuracy   | Notes                                                                                        |
|-------------------------------------------------------------------------------------------------------------------------|-------|------------|----------------------------------------------------------------------------------------------|
| **English**                                                                                               |       |            |  |
| [vosk-model-en-us-aspire-0.2](http://alphacephei.com/kaldi/models/vosk-model-en-us-aspire-0.2.zip)        |  1.4G |   TBD      | Trained on Fisher + more or less recent LM. Should be pretty good for generic US English transcription |
| [vosk-model-small-en-us-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.3.zip)          |  36M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Chinese**                                                                                                   |       |            |  |
| [vosk-model-cn-0.1.zip](http://alphacephei.com/kaldi/models/vosk-model-cn-0.1.zip)                        |  195M |   TBD      | Big narrowband Chinese model for server processing                                           |
| [vosk-model-small-cn-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-cn-0.3.zip)                |  32M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Russian**                                                                                                   |       |            |  |
| [vosk-model-ru-0.10.zip](http://alphacephei.com/kaldi/models/vosk-model-ru-0.10.zip)                      |  2.5G |   TBD      | Big narrowband Russian model for server processing                                           |
| [vosk-model-small-ru-0.4](http://alphacephei.com/kaldi/models/vosk-model-small-ru-0.4.zip)                |  39M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **French**                                                                                                |       |            |  |
| [vosk-model-small-fr-pguyot-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-fr-pguyot-0.3.zip)                |  39M  |   TBD      | Lightweight wideband model for Android and RPi trained by [Paul Guyot](https://github.com/pguyot/zamia-speech/releases) |
| **German**                                                                                                |       |            |  |
| [tuda-de](http://ltdata1.informatik.uni-hamburg.de/kaldi_tuda_de/de_400k_nnet3chain_tdnn1f_2048_sp_bi.tar.bz2)    |  566M |   TBD      | Wideband server model from [tuda-de](https://github.com/uhh-lt/vosk-model-tuda-de)            |
| [vosk-model-small-de-zamia-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-de-zamia-0.3.zip)            |  49M  |   TBD      | Lightweight wideband model for Android and RPi                                           |
| **Spanish**                                                                                                |       |            |  |
| [vosk-model-small-es-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-es-0.3.zip)                |  33M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Portuguese**                                                                                                |       |            |  |
| [vosk-model-small-pt-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-pt-0.3.zip)                |  31M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Greek**                                                                                                |       |            |  |
| [vosk-model-el-gr-0.6.zip](http://alphacephei.com/kaldi/models/vosk-model-el-gr-0.6.zip)                  |  1.1G |   TBD      | Big narrowband Greek model for server processing, not extremely accurate though        |
| **Turkish**                                                                                                |       |            |  |
| [vosk-model-small-tr-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-tr-0.3.zip)                |  35M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Vietnamese**                                                                                                |       |            |  |
| [vosk-model-small-vn-0.3](http://alphacephei.com/kaldi/models/vosk-model-small-vn-0.3.zip)                |  32M  |   TBD      | Lightweight wideband model for Android and RPi                                               |
| **Speaker identification model**                                                                          |       |            |                                                                                              |
| [vosk-model-spk-0.3](http://alphacephei.com/kaldi/models/vosk-model-spk-0.3.zip)                          |  13M  |   TBD      | Model for speaker identification, should work for all languages                              |


## Other models

Other places where you can check for models which might be compatible:

  * http://kaldi-asr.org/models.html - variety of models from Kaldi - librispeech, aspire, chinese models
  * https://github.com/daanzu/kaldi-active-grammar/blob/master/docs/models.md - Big dictation models
  * http://zamia-speech.org/asr/ - German and English model from Zamia
  * https://github.com/pguyot/zamia-speech/releases - French models for Zamia
  * https://github.com/opensource-spraakherkenning-nl/Kaldi_NL - Dutch model
  * https://montreal-forced-aligner.readthedocs.io/en/latest/pretrained_models.html (GMM models, not compatible but might be still useful)
  * https://github.com/goodatlas/zeroth - Korean Kaldi (just a recipe and data to train)
  * https://github.com/undertheseanlp/automatic_speech_recognition - Vietnamese Kaldi project

## Training your own model

You can train your model with Kaldi toolkit. The training is pretty standard - you need tdnn nnet3 model with ivectors. You can
check mini_librispeech recipe for details. Some notes on training:

  * For smaller mobile models watch number of parameters
  * Train the model without pitch. It might be helpful for small amount of data, but for large database it doesn't give the advantage
but complicates the processing and increases response time.
  * Train ivector of dim 30 instead of standard 100 to save memory of mobile models.

## Model structure

Once you trained the model arrange the files according to the following layout (see en-us-aspire for details):

  * `am/final.mdl` - acoustic model
  * `conf/mfcc.conf` - mfcc config file. Make sure you take mfcc_hires.conf version if you are using hires model (most external ones)
  * `conf/model.conf` - provide default decoding beams and silence phones. you have to create this file yourself, it is not present in kaldi model
  * `ivector/final.dubm` - take ivector files from ivector extractor (optional folder if the model is trained with ivectors)
  * `ivector/final.ie`
  * `ivector/final.mat`
  * `ivector/splice.conf`
  * `ivector/global_cmvn.stats`
  * `ivector/online_cmvn.conf`
  * `graph/phones/word_boundary.int` - from the graph
  * `graph/HCLG.fst` - this is the decoding graph, if you are not using lookahead
  * `graph/HCLr.fst` - use Gr.fst and HCLr.fst instead of one big HCLG.fst if you want to run rescoring
  * `graph/Gr.fst`
  * `graph/phones.txt` - from the graph
  * `graph/words.txt` - from the graph
  * `rescore/G.carpa` - carpa rescoring is optional but helpful in big models. Usually located inside data/lang_test_rescore
  * `rescore/G.fst` - also optional if you want to use rescoring

