require "ffi"

module Vosk
    module C
    extend FFI::Library
    # FIXME: Load same way as in Python, test on Windows
    # This second option, 'vosk', allows system-wide installed library to be loaded.
    # I see you search /usr/share/vosk, so I guess it's supported somehow.
    # It'll allow the gem to be used on systems not supported in pre-compiled releases.
    # (in fact, we only need the first in a pre-compiled release and the second otherwise,
    # but not worth the effort to put more configuration in the build stage - not possible without hacks)
    # But when we load a lib not shipped with the gem itself, we (might) need to ensure it's a compatible version
    # Note: options in the array are alternatives, only the first found is loaded
    # Note: probably needs RubyInstaller::Runtime.add_dll_directory on Windows - if FFI::Platform.windows?
    ffi_lib [File.join(__dir__, FFI.map_library_name("vosk")), "vosk"]

    class VoskModel < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create a model" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_model_free(ptr)
      end
    end

    class VoskSpkModel < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create a speaker model" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_spk_model_free(ptr)
      end
    end

    VoskEndpointerMode = enum(
      :VoskEndpointerMode,
      [
        :default, 0,
        :short, 1,
        :long, 2,
        :very_long, 3,
      ]
    )

    class VoskRecognizer < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create a recognizer" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_recognizer_free(ptr)
      end
    end

    class VoskBatchModel < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create a model" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_batch_model_free(ptr)
      end
    end

    class VoskBatchRecognizer < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create a recognizer" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_batch_recognizer_free(ptr)
      end
    end

    class VoskTextProcessor < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, "Failed to create processor" if ptr.null?

        super
      end

      def self.release(ptr)
        C.vosk_text_processor_free(ptr)
      end
    end

    attach_function :vosk_model_new, [:string], VoskModel
    attach_function :vosk_model_free, [VoskModel], :void
    attach_function :vosk_model_find_word, [VoskModel, :string], :int

    attach_function :vosk_spk_model_new, [:string], VoskSpkModel
    attach_function :vosk_spk_model_free, [VoskSpkModel], :void

    attach_function :vosk_recognizer_new, [VoskModel, :float], VoskRecognizer
    attach_function :vosk_recognizer_new_spk, [VoskModel, :float, VoskSpkModel], VoskRecognizer
    attach_function :vosk_recognizer_new_grm, [VoskModel, :float, :string], VoskRecognizer
    attach_function :vosk_recognizer_set_spk_model, [VoskRecognizer, VoskSpkModel], :void
    attach_function :vosk_recognizer_set_grm, [VoskRecognizer, :string], :void
    attach_function :vosk_recognizer_set_max_alternatives, [VoskRecognizer, :int], :void
    attach_function :vosk_recognizer_set_words, [VoskRecognizer, :int], :void
    attach_function :vosk_recognizer_set_partial_words, [VoskRecognizer, :int], :void
    attach_function :vosk_recognizer_set_nlsml, [VoskRecognizer, :int], :void
    # TODO: remove this, it was needed only because I used libvosk from Python package
    if Gem::Version.new(VERSION) >= Gem::Version.new("0.3.46")
      attach_function :vosk_recognizer_set_endpointer_mode, [VoskRecognizer, VoskEndpointerMode], :void
      attach_function :vosk_recognizer_set_endpointer_delays, [VoskRecognizer, :float, :float, :float], :void
    end
    attach_function :vosk_recognizer_accept_waveform, [VoskRecognizer, :buffer_in, :int], :int
    # vosk_recognizer_accept_waveform_s; vosk_recognizer_accept_waveform_f - skipped
    attach_function :vosk_recognizer_result, [VoskRecognizer], :string
    attach_function :vosk_recognizer_partial_result, [VoskRecognizer], :string
    attach_function :vosk_recognizer_final_result, [VoskRecognizer], :string
    attach_function :vosk_recognizer_reset, [VoskRecognizer], :void
    attach_function :vosk_recognizer_free, [VoskRecognizer], :void

    attach_function :vosk_set_log_level, [:int], :void
    attach_function :vosk_gpu_init, [], :void
    attach_function :vosk_gpu_thread_init, [], :void

    attach_function :vosk_batch_model_new, [:string], VoskBatchModel
    attach_function :vosk_batch_model_free, [VoskBatchModel], :void
    attach_function :vosk_batch_model_wait, [VoskBatchModel], :void

    attach_function :vosk_batch_recognizer_new, [VoskBatchModel, :float], VoskBatchRecognizer
    attach_function :vosk_batch_recognizer_free, [VoskBatchRecognizer], :void
    attach_function :vosk_batch_recognizer_accept_waveform, [VoskBatchRecognizer, :buffer_in, :int], :void
    # vosk_batch_recognizer_set_nlsml - skipped
    attach_function :vosk_batch_recognizer_finish_stream, [VoskBatchRecognizer], :void
    attach_function :vosk_batch_recognizer_front_result, [VoskBatchRecognizer], :string
    attach_function :vosk_batch_recognizer_pop, [VoskBatchRecognizer], :void
    attach_function :vosk_batch_recognizer_get_pending_chunks, [VoskBatchRecognizer], :int

    # https://github.com/ffi/ffi/issues/467
    class OwnedString
      extend FFI::DataConverter
      native_type :strptr

      def self.to_native(_value, _context)
        raise TypeError, "owned_string can't be used for input"
      end

      def self.from_native((str, ptr), _context)
        C.free(ptr)
        str
      end
    end

    typedef OwnedString, :owned_string
    attach_function :free, [:pointer], :void

    # TODO: remove this, it was needed only because I used libvosk from Python package
    if Gem::Version.new(VERSION) >= Gem::Version.new("0.3.48")
      attach_function :vosk_text_processor_new, [:string, :string], VoskTextProcessor
      attach_function :vosk_text_processor_free, [VoskTextProcessor], :void
      # Note: you have a memory leak here in your python version, needs to be
      # ptr = _c.vosk_text_processor_itn(self._handle, text.encode('utf-8'))
      # str = _ffi.string(ptr).decode('utf-8')
      #  _ffi.gc(ptr, _c.free)  # or call libc free directly
      attach_function :vosk_text_processor_itn, [VoskTextProcessor, :string], :owned_string
    end
  end

  private_constant :C
end
