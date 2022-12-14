To try this package do the following steps:

On Linux (we download library and set LD_LIBRARY_PATH)

```
git clone https://github.com/alphacep/vosk-api
cd vosk-api/go/example
wget https://github.com/alphacep/vosk-api/releases/download/v0.3.45/vosk-linux-x86_64-0.3.45.zip
unzip vosk-linux-x86_64-0.3.45.zip
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
cp ../../python/example/test.wav .
VOSK_PATH=`pwd`/vosk-linux-x86_64-0.3.45 LD_LIBRARY_PATH=$VOSK_PATH CGO_CPPFLAGS="-I $VOSK_PATH" CGO_LDFLAGS="-L $VOSK_PATH" go run . -f test.wav
```

for Windows (we place DLLs in current folder where linker finds them):

```
git clone https://github.com/alphacep/vosk-api
cd vosk-api/go/example
wget https://github.com/alphacep/vosk-api/releases/download/v0.3.45/vosk-linux-x86_64-0.3.45.zip
unzip vosk-linux-x86_64-0.3.45.zip
cp vosk-linux-x86_64-0.3.45/*.dll .
cp vosk-linux-x86_64-0.3.45/*.h .
wget https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip
unzip vosk-model-small-en-us-0.15.zip
mv vosk-model-small-en-us-0.15 model
cp ../../python/example/test.wav .
VOSK_PATH=`pwd` LD_LIBRARY_PATH=$VOSK_PATH CGO_CPPFLAGS="-I $VOSK_PATH" CGO_LDFLAGS="-L $VOSK_PATH -lvosk -lpthread -dl" go run . -f test.wav
```
