#!/usr/bin/env ruby
# frozen_string_literal: true

require "vosk"

SAMPLE_RATE = 16_000

Vosk.log_level = -1

model = Vosk::Model.new(lang: "en-us")
rec = Vosk::KaldiRecognizer.new(model, SAMPLE_RATE)
rec.words = true

IO.popen(["ffmpeg", "-loglevel", "quiet", "-i", "audio.mp4",
          "-ar", SAMPLE_RATE.to_s, "-ac", "1", "-f", "s16le", "-",]) do |stream|
  puts rec.srt_result(stream)
end
