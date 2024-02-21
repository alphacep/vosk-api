# frozen_string_literal: true

require "vosk"
require "json"
require "net/http"

MODEL = "vosk-model-small-en-us-0.15"

unless File.directory?(MODEL)
  puts "Downloading #{MODEL}..."
  model_zip = Net::HTTP.get(URI("https://alphacephei.com/vosk/models/#{MODEL}.zip"))
  File.binwrite("model.zip", model_zip)
  system "unzip model.zip", exception: true
  File.delete("model.zip")
  puts "Done"
end

# Vosk::FFI.vosk_set_log_level(-1)

model      = Vosk::FFI.vosk_model_new(MODEL)
recognizer = Vosk::FFI.vosk_recognizer_new(model, 16_000.0)

file = File.open("../python/example/test.wav", "r")
file.seek 44, IO::SEEK_SET

audio = file.read

Vosk::FFI.vosk_recognizer_accept_waveform(recognizer, audio, audio.size)

result = Vosk::FFI.vosk_recognizer_final_result(recognizer).to_s

puts JSON.parse(result)
