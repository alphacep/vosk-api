Java API sample

Doesn't work on Windows or Mac yet, help to prepare the packaged jars is welcome.

For now to try it:

On Linux you can do

   1. Build recent kaldi
   1. `git clone https://github.com/alphacep/vosk-api`
   1. `cd vosk-api/java`
   1. `export KALDI_ROOT=<KALDI_ROOT>`
   1. `export JAVA_HOME=<JAVA_HOME>`
   1. `make`
   1. `make run`

For details of the code you can check:

https://github.com/alphacep/vosk-api/blob/master/java/test/DecoderTest.java
