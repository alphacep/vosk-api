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

## Python module build

First build Kaldi

```
git clone https://github.com/alphacep/kaldi
cd kaldi
git checkout lookahead
cd tools
make -j 10
extras/install_openblas.sh
cd ../src
./configure --mathlib=OPENBLAS --shared --use-cuda=no
make -j 10
```
Then python module

```
cd python
python3 setup.py install
```


