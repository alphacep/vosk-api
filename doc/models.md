# Models

This is the list of models compatible with Vosk-API.

To add a new model here create an issue on Github.

| Model                                                                                                     | Size  | Accuracy   | Notes                                                                                        |
|-------------------------------------------------------------------------------------------------------------------------|-------|------------|----------------------------------------------------------------------------------------------|
| **English**                                                                                               |       |            |  |
| [vosk-model-en-us-aspire-0.1](http://alphacephei.com/kaldi/models/vosk-model-en-us-aspire-0.1.zip)        |  363M |   TBD      | Trained on Fisher + more or less recent LM. Pretty outdated but still ok even even for calls |
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

Other places where you can check for models which might be compatible:

  * http://kaldi-asr.org/models.html
  * https://github.com/daanzu/kaldi-active-grammar/blob/master/docs/models.md
  * http://zamia-speech.org/asr/
  * https://github.com/opensource-spraakherkenning-nl/Kaldi_NL - Dutch model
  * https://montreal-forced-aligner.readthedocs.io/en/latest/pretrained_models.html (gmm models, not compatible but might be still useful)
