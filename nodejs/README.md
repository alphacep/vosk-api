This is an FFI-NAPI wrapper for the Vosk library.

## Usage

```sh
npm install vosk
```

It mostly follows Vosk interface, some methods are not yet fully implemented.

To use it you need to compile libvosk library, see Python module build
instructions for details. You can find prebuilt library inside python
wheel.

## About

Vosk is an offline open source speech recognition toolkit. It enables
speech recognition models for 17 languages and dialects - English, Indian
English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish,
Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino.

Vosk models are small (50 Mb) but provide continuous large vocabulary
transcription, zero-latency response with streaming API, reconfigurable
vocabulary and speaker identification.

Vosk supplies speech recognition for chatbots, smart home appliances,
virtual assistants. It can also create subtitles for movies,
transcription for lectures and interviews.

Vosk scales from small devices like Raspberry Pi or Android smartphone to
big clusters.

# Documentation

For installation instructions, examples and documentation visit [Vosk
Website](https://alphacephei.com/vosk). See also our project on
[Github](https://github.com/alphacep/vosk-api).

# Development

This repository uses `yarn`, therefore:

```sh
yarn install
yarn download:lib # Requires wget
```

**Note: `yarn download:lib` downloads the prebuild vosk library that is also included in the published version of this library on npm. If you need the latest Vosk-API features that might not be included in these binaries yet, you'll have to build the Vosk-API from source and create the `nodejs/lib` directory yourself.**

In order to start typescript compilation in watch mode you'll need to place these in the `nodejs` directory:

- A `model` directory with one of the models available [here](https://alphacephei.com/vosk/models)
- A `spk_model` directory with the [speaker identification model](https://alphacephei.com/vosk/models/vosk-model-spk-0.4.zip)
- A `test.wav` with some speech matching the language of the `model`

To start typescript compilation in watch mode run:

```sh
yarn start
```

...this will automatically rebuild the library in memory and execute `watch.ts` afterwards which will decode `test.wav` and log the results.

To build the library and create the `dist` directory containing the library in pure javascript simply call:

```sh
yarn build
```
