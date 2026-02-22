#!/usr/bin/env ruby
# frozen_string_literal: true

require "vosk"
require "wavefile"

# You can set log level to -1 to disable debug messages
Vosk.log_level = 0

WaveFile::Reader.new(ARGV[0]) do |reader|
  reader_format = reader.format
  unless reader_format.channels == 1 && reader_format.bits_per_sample == 16 && reader_format.sample_format == :pcm
    puts("Audio file must be WAV format mono PCM.")
    exit(1)
  end

  model = Vosk::Model.new(lang: "en-us")

  # You can also init model by name or with a folder path
  # model = Model(model_name: "vosk-model-en-us-0.21")
  # model = Model(model_path: "models/en")

  rec = Vosk::KaldiRecognizer.new(model, reader_format.sample_rate)
  rec.words = true
  rec.partial_words = true

  reader.each_buffer(4000) do |buffer|
    data = buffer.samples.pack(WaveFile::PACK_CODES.dig(:pcm, 16))

    if rec.accept_waveform(data).nonzero?
      puts rec.result
    else
      puts rec.partial_result
    end
  end
  puts rec.final_result
end
