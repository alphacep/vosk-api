# frozen_string_literal: true

require "fiddle"
require "fiddle/import"
require "rbconfig"

module Vosk
  module FFI
    extend Fiddle::Importer

    begin
      lib = "libvosk.#{RbConfig::CONFIG["SOEXT"]}"
      dlload(lib)
    rescue Fiddle::DLError => e
      abort <<~MSG
        Could not find `#{lib}`.

        Install Vosk-api, then try again.

        Error: #{e&.cause&.message || e&.message || e.inspect}
      MSG
    end

    # rubocop:disable Layout/LineLength

    extern "VoskModel *vosk_model_new(const char *model_path);"
    extern "VoskRecognizer *vosk_recognizer_new(VoskModel *model, float sample_rate);"
    extern "int vosk_recognizer_accept_waveform(VoskRecognizer *recognizer, const char *data, int length);"
    extern "const char *vosk_recognizer_result(VoskRecognizer *recognizer);"
    extern "const char *vosk_recognizer_final_result(VoskRecognizer *recognizer);"
    extern "void vosk_recognizer_reset(VoskRecognizer *recognizer);"
    extern "void vosk_recognizer_free(VoskRecognizer *recognizer);"
    extern "void vosk_model_free(VoskModel *model);"
    extern "void vosk_set_log_level(int log_level);"

    # rubocop:enable Layout/LineLength
  end
end
