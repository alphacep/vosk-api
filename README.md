[![Build Status](https://travis-ci.com/alphacep/vosk-api.svg?branch=master)](https://travis-ci.com/alphacep/vosk-api)

Language bindings for Vosk and Kaldi to access speech recognition from various languages and on various platforms

  * Python on Linux, Windows and RPi
  * Node
  * Android
  * iOS

## Android build

```
cd android
gradle build
```

Please note that medium blog post about 64-bit is not relevant anymore, the script builds x86, arm64 and armv7 libraries automatically without any modifications.

## Python installation from Pypi

The easiest way to install vosk api is with pip. You do not have to compile anything. We currently support only Linux on x86_64 and Raspberry Pi. Other systems (windows, mac) will come soon.

Make sure you have newer pip and python:

  * Python version >= 3.4
  * pip version >= 19.0

Uprade python and pip if needed. Then install vosk on Linux with a simple command

```
pip3 install vosk
```

## Compilation from source

If you still want to build from scratch, you can compile Kaldi and Vosk yourself. The compilation is straightforward but might be a little confusing for newbie. In case you want to follow this, please watch the errors.

#### Kaldi compilation for local python, node and java modules

```
git clone -b lookahead --single-branch https://github.com/alphacep/kaldi
cd kaldi/tools
make
```

install all dependencies and repeat `make` if needed

```
extras/install_openblas.sh
cd ../src
./configure --mathlib=OPENBLAS --shared --use-cuda=no
make -j 10
```

#### Python module build

Then build the python module

```
export KALDI_ROOT=<KALDI_ROOT>
cd python
python3 setup.py install
```

#### Java example API build

Or Java

```
cd java && KALDI_ROOT=<KALDI_ROOT> make
wget https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-en-us-0.3.tar.gz
tar xf alphacep-model-android-en-us-0.3.tar.gz 
mv alphacep-model-android-en-us-0.3 model
make run
```

#### C# build

Or C#

```
cd csharp && KALDI_ROOT=<KALDI_ROOT> make
wget https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-en-us-0.3.tar.gz
tar xf alphacep-model-android-en-us-0.3.tar.gz 
mv alphacep-model-android-en-us-0.3 model
mono test.exe
```

## Running the example code with python

Run like this:

```
cd vosk-api/python/example
wget https://github.com/alphacep/kaldi-android-demo/releases/download/2020-01/alphacep-model-android-en-us-0.3.tar.gz
tar xf alphacep-model-android-en-us-0.3.tar.gz 
mv alphacep-model-android-en-us-0.3 model-en
python3 ./test_simple.py test.wav
```

There are models for other languages (English, Chinese, Spanish, Portuguese, German, French, Russian) available too at https://github.com/alphacep/kaldi-android-demo/releases

To run with your audio file make sure it has proper format - PCM 16khz 16bit mono, otherwise decoding will not work.

You can find other examples of using a microphone, decoding with a fixed small vocabulary or speaker identification setup in  [python/example subfolder](https://github.com/alphacep/vosk-api/tree/master/python/example)

## Contact Us

If you have any questions, feel free to

   * Post an issue here on github
   * Send us an e-mail at [contact@alphacephei.com](mailto:contact@alphacephei.com)
   * Join our group dedicated to speech recognition on Telegram [@speech_recognition](https://t.me/speech_recognition)
   
