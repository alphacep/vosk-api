# freebsd 12.3 vosk-api build

echo '
Build Vosk-API for FreeBSD 12.3 (and possibly later too).

Please review this script before executing.  A number of packages
will be installed, and some soft links made in /bin and /usr/local/{bin,lib}.

Expect 20-120 minutes to build everything.  Sudo is required for installing
packages and making soft links.

Press ^c to exit, or return to start building.
'
read junk

set -ex

# pkgs required
sudo pkg install git cmake gmake libtool automake autoconf autotools \
    libatomic_ops gsed python38 py38-setuptools py38-wheel py38-pip-run \
    wget bash curl sox


# required:
# skullduggery soft links to make build run smoother and less patching
sudo ln -s /usr/local/lib/libatomic_ops.a /usr/lib/libatomic.a
sudo ln -s /usr/local/bin/bash /bin/bash
sudo ln -s /usr/local/bin/gmake /usr/local/bin/make
sudo ln -s /usr/local/bin/python3.8 /usr/local/bin/python3
# make sure to pick up our soft link first
PATH=/usr/local/bin:$PATH


# create a build dir for everything
mkdir build
cd build
BUILD_ROOT=$PWD


# from here, mostly from vosk-api/travis/Dockerfile.manylinux
# sed and patch used to include FreeBSD as supported OS and to make minor adjustments

git clone https://github.com/alphacep/vosk-api.git
git clone -b vosk --single-branch https://github.com/alphacep/kaldi 

# Build kaldi tools
cd $BUILD_ROOT/kaldi/tools 
git clone -b v0.3.13 --single-branch https://github.com/xianyi/OpenBLAS 
git clone -b v3.2.1  --single-branch https://github.com/alphacep/clapack 

gmake -C OpenBLAS ONLY_CBLAS=1 DYNAMIC_ARCH=1 TARGET=NEHALEM USE_LOCKING=1 USE_THREAD=0 all 
gmake -C OpenBLAS PREFIX=$PWD/OpenBLAS/install install 

mkdir -p clapack/BUILD && cd clapack/BUILD && cmake .. && gmake -j 10 && cp `find . -name "*.a"`  ../../OpenBLAS/install/lib 

cd $BUILD_ROOT/kaldi/tools 
git clone --single-branch https://github.com/alphacep/openfst openfst 
cd openfst 
autoreconf -i 
CFLAGS="-g -O3" ./configure --prefix=$BUILD_ROOT/kaldi/tools/openfst --enable-static --enable-shared --enable-far --enable-ngram-fsts --enable-lookahead-fsts --with-pic --disable-bin 
gmake -j 10 
gmake install 


# Build kaldi main
cd $BUILD_ROOT/kaldi/src 

./configure --mathlib=OPENBLAS_CLAPACK --shared --use-cuda=no 
gsed -i 's:-msse -msse2:-msse -msse2:g' kaldi.mk 
gsed -i 's: -O1 : -O3 :g' kaldi.mk 

gmake -j 4 online2 lm rnnlm 



# Build vosk-api shared lib

cd $BUILD_ROOT/vosk-api/src
# FreeBSD needs -lexecinfo for python interface
KALDI_ROOT=$BUILD_ROOT/kaldi EXTRA_LDFLAGS='-lexecinfo' gmake


# optional-  build and test vosk C interface
cd $BUILD_ROOT/vosk-api/c
gmake

wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
cp ../python/example/test.wav  .
./test_vosk

# install the python interface
cd $BUILD_ROOT/vosk-api/python
# install python module
sudo python3.8 setup.py install


# test the python interface
cd examples
# wget https://alphacephei.com/kaldi/models/vosk-model-small-en-us-0.15.zip
# or, if you tested the vosk C interface, above, just grab the model.zip from there
cp ../../c/vosk-model-small-en-us-0.15.zip .
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model

python3.8 test_simple.py test.wav


# clean up soft links
sudo rm /usr/lib/libatomic.a
sudo rm /bin/bash
sudo rm /usr/local/bin/make
sudo rm /usr/local/bin/python3

# done

