# bundle exec ruby test_captcha.rb /home/vladimir/Documents/course4/diplom/vosk-api/python/example/378dcdebf942e82cc0a6f199a6182910.wav

require_relative 'lib/vosk'
require 'wavefile'
require 'json'

Vosk.set_log_level -1

WaveFile::Reader.new(ARGV[0]) do |reader|
  f = reader.format
  if f.channels != 1 || f.bits_per_sample != 16 || f.sample_format != :pcm
    puts('Audio file must be WAV format mono PCM.')
    exit(1)
  end

  model = Vosk::Model.new(model_name: 'vosk-model-small-en-us-0.4')

  trigger_words = ['please enter the number you hear', 'please type the numbers you hear']
  numbers = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'zero']

  # You can also specify the possible word or phrase list as JSON list,
  # the order doesn't have to be strict
  rec = Vosk::KaldiRecognizer.new(
    model, f.sample_rate,
    JSON.generate([*trigger_words, *numbers, '[unk]'])
  )
  rec.set_words(true)

  reader.each_buffer(4000) do |buffer|
    # 16 bits
    data = buffer.samples.pack('s<*')
    next unless rec.accept_waveform(data).nonzero?

    print JSON.parse(rec.result)['text']
    print ', '
  end
  puts JSON.parse(rec.final_result())['text']
end
