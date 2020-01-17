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

Make sure you have pip:

  * Python version >= 3.4
  * pip version >= 19.0

Uprade python and pip if needed. Then install vosk on Linux with a simple command

```
pip install vosk
```

## Python module build

First build Kaldi

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

Then build python build module

```
export KALDI_ROOT=<KALDI_ROOT>
cd python
python3 setup.py install
```
