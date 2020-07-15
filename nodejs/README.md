Installation requires vosk-api checkout, it doesn't yet work with `npm
install vosk`. We have to figure out how to properly distribute native
modules for Vosk.

The build tested with node-0.10.15, node-0.12 is not yet supported by swig.

Still, you need swig of newest version 4.0.1

Build like this

```
npm install --kaldi_root=/home/suser/kaldi
```

Then test with

```
cd example
node test.js
```
