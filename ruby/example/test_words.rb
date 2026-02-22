#!/usr/bin/env ruby
# frozen_string_literal: true

require "vosk"
require "wavefile"

WaveFile::Reader.new(ARGV[0]) do |reader|
  reader_format = reader.format
  unless reader_format.channels == 1 && reader_format.bits_per_sample == 16 && reader_format.sample_format == :pcm
    puts("Audio file must be WAV format mono PCM.")
    exit(1)
  end

  model = Vosk::Model.new(lang: "en-us")

  # You can also specify the possible word or phrase list as JSON list,
  # the order doesn't have to be strict
  rec = Vosk::KaldiRecognizer.new(
    model, reader_format.sample_rate,
    '["oh one two three", "four five six", "seven eight nine zero", "[unk]"]',
  )

  reader.each_buffer(4000) do |buffer|
    data = buffer.samples.pack(WaveFile::PACK_CODES.dig(:pcm, 16))

    if rec.accept_waveform(data).nonzero?
      puts rec.result
      rec.grammar = '["one zero one two three oh", "four five six", "seven eight nine zero", "[unk]"]'
    else
      puts rec.partial_result
    end
  end
  puts rec.final_result
end
