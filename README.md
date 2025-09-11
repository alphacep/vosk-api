# Vosk Speech Recognition Toolkit

Vosk is an offline open source speech recognition toolkit. It enables
speech recognition for 20+ languages and dialects - English, Indian
English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish,
Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino,
Ukrainian, Kazakh, Swedish, Japanese, Esperanto, Hindi, Czech, Polish.
More to come.

Vosk models are small (50 Mb) but provide continuous large vocabulary
transcription, zero-latency response with streaming API, reconfigurable
vocabulary and speaker identification.

Speech recognition bindings implemented for various programming languages
like Python, Java, Node.JS, C#, C++, Rust, Go and others.

Vosk supplies speech recognition for chatbots, smart home appliances,
virtual assistants. It can also create subtitles for movies,
transcription for lectures and interviews.

Vosk scales from small devices like Raspberry Pi or Android smartphone to
big clusters.

# Building for Fedora 41 or later

In order to build it on Fedora 41 using the libraries that are provided by the distro, you need to install kaldi, after building from the source (no kaldi packages for fedora exist).

then build the package as follows:

```
cmake -S ./ -Bbuild/Release -DBuildForFedora=ON -DBUILD_SHARED_LIBS=ON
cmake --build ./build/Release
```


# Documentation

For installation instructions, examples and documentation visit [Vosk
Website](https://alphacephei.com/vosk).
