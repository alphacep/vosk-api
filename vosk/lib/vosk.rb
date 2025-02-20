# frozen_string_literal: true

require_relative 'vosk/version'
require 'ffi'
require 'httparty'
# gem 'progressbar'
require 'progressbar'
require 'bytesize'
# gem 'rubyzip', '~> 2.4', '>= 2.4.1'
require 'zip'
require 'fileutils'

module Vosk
  class Error < StandardError; end

  # Remote location of the models and local folders
  MODEL_PRE_URL = 'https://alphacephei.com/vosk/models/'
  MODEL_LIST_URL = "#{MODEL_PRE_URL}model-list.json"
  # TODO: Test on Windows
  MODEL_DIRS = [
    ENV['VOSK_MODEL_PATH'], '/usr/share/vosk',
    File.join(Dir.home, 'AppData/Local/vosk'), File.join(Dir.home, '.cache/vosk'),
  ]

  # Different from Python: no need to print inside the method, simply +puts Vosk.models+
  def self.models
    response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
    response.map { |model| model['name'] }
  end

  # Different from Python: no need to print inside the method, simply +puts Vosk.languages+
  def self.languages
    response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
    response.map { |model| model['lang'] }.uniq
  end

  module C
    extend FFI::Library
    # FIXME: Load same way as in Python, test on Windows
    # This second option, 'vosk', allows system-wide installed library to be loaded.
    # I see you search /usr/share/vosk, so I guess it's supported somehow.
    # It'll allow the gem to be used on systems not supported in pre-compiled releases.
    # (in fact, we only need the first in a pre-compiled release and the second otherwise,
    # but not worth the effort to put more configuration in the build stage - not possible without hacks)
    # But when we load a lib not shipped with the gem itself, we (migth) need to ensure it's a compatible version
    # Note: options in the array are alternatives, only the first found is loaded
    ffi_lib [File.join(__dir__, FFI.map_library_name('vosk')), 'vosk']

    class VoskModel < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, 'Failed to create a model' if ptr.null?
        super
      end

      def self.release(ptr)
        C.vosk_model_free(ptr) unless ptr.null?
      end
    end

    class VoskSpkModel < FFI::AutoPointer
      def self.from_native(ptr, _ctx)
        raise Error, 'Failed to create a speaker model' if ptr.null?
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

    attach_function :vosk_model_new, [:string], VoskModel
    attach_function :vosk_model_free, [VoskModel], :void
    attach_function :vosk_model_find_word, [VoskModel, :string], :int
    # vosk_recognizer_new, vosk_recognizer_new_spk, vosk_recognizer_new_grm

    attach_function :vosk_spk_model_new, [:string], VoskSpkModel
    attach_function :vosk_spk_model_free, [VoskSpkModel], :void
    # attach_function :vosk_recognizer_new_spk, [VoskModel, :float :VoskSpkModel], VoskRecognizer
    # vosk_recognizer_set_spk_model

    attach_function :vosk_set_log_level, [:int], :void
    attach_function :vosk_gpu_init, [], :void
    attach_function :vosk_gpu_thread_init, [], :void

    # attach_function :vosk_recognizer_new, [:pointer, :int], :pointer
    # attach_function :vosk_recognizer_free, [:pointer], :void
    # attach_function :vosk_recognizer_accept_waveform, [:pointer, :pointer, :int], :bool
    # attach_function :vosk_recognizer_result, [:pointer], :string
    # attach_function :vosk_recognizer_final_result, [:pointer], :string
    # attach_function :vosk_recognizer_reset, [:pointer], :void
  end

  private_constant :C

  class Model
    def initialize(path: nil)
      @handle = C.vosk_model_new(path)
    end

    def find_word(word)
      C.vosk_model_find_word(@handle, word)
    end

    def download_model(name)
      dirname = File.dirname(name)
      # Python version won't try to create the directory if a file with the same name exists
      FileUtils.makedirs(dirname) unless Dir.exists?(dirname)
    end

    def download_progress_bar(name)
      # Why add MODEL_PRE_URL and then split it away?
      desc = "#{File.basename(name)}.zip"
      begin
        progressbar = ProgressBar.create(
          title: desc, total: nil, progress_mark: '█',
          # | 105M/191G [01:39<46:44:25, 1.22MB/s]
          format: '%t: %j%%|%B| %c/%u [%a<%l, %R/sec]', # or '%r KB/sec' if rate_scale doesn't work,
          rate_scale: lambda { |rate| ByteSize.new(rate).to_s },
        )
        bsize, tsize = yield
        progressbar.total = tsize if tsize && tsize >= progressbar.progress
        progressbar.progress += bsize
      ensure
        progressbar&.finish
      end
    end
  end

  class SpkModel
    def initialize(path:)
      @handle = C.vosk_spk_model_new(path)
    end
  end

  class EndpointerMode
    C::VoskEndpointerMode.symbol_map.each do |name, value|
      const_set(name.upcase, value)
    end
  end

  def self.set_log_level(level)
    C.vosk_set_log_level(level)
  end

  def self.gpu_init
    C.vosk_gpu_init
  end

  def self.gpu_thread_init
    C.vosk_gpu_thread_init
  end
end

Vosk.set_log_level(-1)
model = Vosk::Model.new(path: '/home/vladimir/.cache/vosk/vosk-model-small-en-us-0.4')
p model.find_word('one')

# Vosk::Model.new(path: '/home/vladimir/.cache/vosk/vosk-model-small-en-us-0.5')
