# Vosk Ruby

Ruby bindings for [Vosk](https://alphacephei.com/vosk/) — an offline speech recognition toolkit supporting 20+ languages.

## Installation

Add to your Gemfile:

```ruby
gem "vosk"
```

Or install directly:

```bash
gem install vosk
```

The gem ships with a precompiled `libvosk` for supported platforms. On other platforms it will attempt to load a system-installed `libvosk`.

## Usage

### Basic transcription

```ruby
require "vosk"
require "wavefile"

# Load a model by language (downloaded automatically if not cached)
model = Vosk::Model.new(lang: "en-us")

# Or by name, or by local path:
# model = Vosk::Model.new(model_name: "vosk-model-small-en-us-0.4")
# model = Vosk::Model.new(model_path: "/path/to/model")

WaveFile::Reader.new("audio.wav") do |reader|
  rec = Vosk::KaldiRecognizer.new(model, reader.format.sample_rate)

  reader.each_buffer(4000) do |buffer|
    data = buffer.samples.pack(WaveFile::PACK_CODES.dig(:pcm, 16))
    if rec.accept_waveform(data).nonzero?
      puts rec.result        # JSON: {"text": "..."}
    else
      puts rec.partial_result  # JSON: {"partial": "..."}
    end
  end
  puts rec.final_result
end
```

Audio must be mono, 16-bit PCM WAV. Use [wavefile](https://github.com/jstrait/wavefile) to read it.

### Grammar / keyword recognition

Pass a JSON array of phrases as the third argument:

```ruby
rec = Vosk::KaldiRecognizer.new(model, sample_rate, '["one two three", "[unk]"]')
```

### Recognizer options

```ruby
rec.words = true          # include per-word timing in results
rec.partial_words = true  # include per-word timing in partial results
rec.max_alternatives = 5  # return n-best list instead of single result
rec.nlsml = true          # return NLSML instead of JSON
```

### SRT subtitle generation

`srt_result` reads raw PCM from any IO stream and returns an SRT-formatted string. Use ffmpeg to decode any audio format on the fly:

```ruby
require "vosk"

SAMPLE_RATE = 16_000

model = Vosk::Model.new(lang: "en-us")
rec = Vosk::KaldiRecognizer.new(model, SAMPLE_RATE)
rec.words = true # required for word-level timestamps

IO.popen(["ffmpeg", "-loglevel", "quiet", "-i", "audio.mp4",
          "-ar", SAMPLE_RATE.to_s, "-ac", "1", "-f", "s16le", "-",]) do |stream|
  puts rec.srt_result(stream)
end
```

The `words_per_line:` keyword controls how many words appear per subtitle line (default: 7):

```ruby
rec.srt_result(stream, words_per_line: 5)
```

### Speaker identification

```ruby
spk_model = Vosk::SpkModel.new("/path/to/spk-model")
rec = Vosk::KaldiRecognizer.new(model, sample_rate)
rec.spk_model = spk_model
```

### Listing available models

```ruby
puts Vosk.models      # all model names
puts Vosk.languages   # all supported language codes
```

### Logging

```ruby
Vosk.log_level = -1   # suppress all output
Vosk.log_level = 0    # default
```

### Transcriber CLI

The gem includes a `vosk-transcriber` executable:

```bash
vosk-transcriber audio.wav
```

## Model storage

Models are cached in `~/.cache/vosk/` by default, or in the directory set by `$VOSK_MODEL_PATH`.

## Development

```bash
bundle install
bundle exec rake spec
```

## License

Apache-2.0
