# frozen_string_literal: true

require "vosk/ffi"

RSpec.describe Vosk::FFI do
  %w[
    vosk_model_new
    vosk_recognizer_new
    vosk_recognizer_accept_waveform
    vosk_recognizer_result
    vosk_recognizer_final_result
    vosk_recognizer_reset
    vosk_recognizer_free
    vosk_model_free
    vosk_set_log_level
  ].each do |method|
    it ".#{method}" do
      expect(described_class).to respond_to(method)
    end
  end
end
