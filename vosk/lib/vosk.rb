# frozen_string_literal: true

require_relative "vosk/version"
require "httparty"
require_relative "vosk/progressbar"
require_relative "vosk/ffi"
require "zip"
require "fileutils"
require "json"

# Vosk speech recognition system
module Vosk
  class Error < StandardError; end

  # Remote location of the models and local folders
  MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
  MODEL_LIST_URL = "#{MODEL_PRE_URL}model-list.json"
  # TODO: Test on Windows
  MODEL_DIRS = [
    ENV.fetch("VOSK_MODEL_PATH", nil), "/usr/share/vosk",
    File.join(Dir.home, "AppData/Local/vosk"), File.join(Dir.home, ".cache/vosk"),
  ].compact.freeze

  # Different from Python: no need to print inside the method, simply use +puts Vosk.models+
  def self.models
    response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
    response.map { |model| model["name"] }
  end

  # Different from Python: no need to print inside the method, simply use +puts Vosk.languages+
  def self.languages
    response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
    response.map { |model| model["lang"] }.uniq
  end

  # Model stores all the data required for recognition
  #  it contains static data and can be shared across processing
  #  threads.
  class Model
    attr_reader :handle

    def initialize(model_path: nil, model_name: nil, lang: nil)
      model_path ||= get_model_path(model_name, lang)
      @handle = C.vosk_model_new(model_path)
    end

    def vosk_model_find_word(word)
      C.vosk_model_find_word(@handle, word)
    end

    private

    def get_model_path(model_name, lang)
      if model_name
        get_model_by_name(model_name)
      else
        get_model_by_lang(lang)
      end
    end

    def get_model_by_name(model_name)
      MODEL_DIRS.each do |directory|
        next unless Dir.exist?(directory)

        entry = Dir.entries(directory).find { |f| f == model_name }
        return File.join(directory, entry) if entry
      end
      response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
      result_model = response.map { |m| m["name"] }.find { |n| n == model_name }
      unless result_model
        # It's not common for Ruby gems to exit the whole process, but I decided to match Python behavior
        puts "model name #{model_name} does not exist"
        exit(1)
      end
      # It always selects the last dir for downloads, ignoring env and windows-specific dir
      dest = File.join(MODEL_DIRS.last, result_model)
      download_model(dest)
      dest
    end

    def get_model_by_lang(lang)
      MODEL_DIRS.each do |directory|
        next unless Dir.exist?(directory)

        entry = Dir.entries(directory).find { |f| f.match?(/\Avosk-model(-small)?-#{Regexp.escape(lang)}/) }
        return File.join(directory, entry) if entry
      end
      response = HTTParty.get(MODEL_LIST_URL, timeout: 10)
      result_model = response.find do |m|
        m["lang"] == lang && m["type"] == "small" && m["obsolete"] == "false"
      end&.dig("name")
      unless result_model
        # It's not common for Ruby gems to exit the whole process, but I decided to match Python behavior
        puts "lang #{lang} does not exist"
        exit(1)
      end
      # It always selects the last dir for downloads, ignoring env and windows-specific dir
      dest = File.join(MODEL_DIRS.last, result_model)
      download_model(dest)
      dest
    end

    # Python param "model_name" is, in fact, a full path
    # rubocop:disable Metrics/MethodLength
    def download_model(model_path)
      dir = File.dirname(model_path)
      # Python version won't try to create the directory if a file with the same name exists
      FileUtils.makedirs(dir)
      model_name = File.basename(model_path)
      zip_path = "#{model_path}.zip"
      url = "#{MODEL_PRE_URL}#{model_name}.zip"

      progressbar = ProgressBar.create(
        # Why add MODEL_PRE_URL and then split it away?
        title: "#{model_name}.zip",
        total: nil,
        progress_mark: "█",
        format: "%t: %j%%|%B| %s/%z [%d<%o, %r/s]",
        rate_scale: ->(rate) { ByteSize.new(rate.to_i).to_s },
      )

      begin
        download_file(url, zip_path) do |bsize, tsize|
          progressbar.total = tsize if tsize && tsize >= progressbar.progress
          progressbar.progress += bsize
        end
        progressbar.finish
      ensure
        progressbar&.stop
      end

      Zip::File.open(zip_path) do |zip_file|
        zip_file.each do |entry|
          entry_path = File.join(dir, entry.name)
          FileUtils.makedirs(File.dirname(entry_path))
          entry.extract(entry_path) { true }
        end
      end

      File.unlink(zip_path)
    end
    # rubocop:enable Metrics/MethodLength

    def download_file(url, dest, &callback)
      File.open(dest, File::CREAT | File::WRONLY | File::TRUNC | File::BINARY) do |file|
        response = HTTParty.get(url, stream_body: true) do |fragment|
          next unless fragment.http_response.is_a?(Net::HTTPSuccess)

          file.write(fragment)
          callback&.call(fragment.bytesize, fragment.http_response["Content-Length"]&.to_i)
        end
        raise HTTParty::ResponseError.new(response), "Code #{response.code}" unless response.success?
      end
    end
  end

  # Speaker model is the same as model but contains the data
  #  for speaker identification.
  class SpkModel
    attr_reader :handle

    def initialize(model_path)
      @handle = C.vosk_spk_model_new(model_path)
    end
  end

  # Endpointer scaling factor
  class EndpointerMode
    C::VoskEndpointerMode.symbol_map.each do |name, value|
      const_set(name.upcase, value)
    end
  end

  # Recognizer object is the main object which processes data.
  #  Each recognizer usually runs in own thread and takes audio as input.
  #  Once audio is processed recognizer returns JSON object as a string
  #  which represent decoded information - words, confidences, times, n-best lists,
  #  speaker information and so on
  class KaldiRecognizer
    # Python version accepts *args, so in case of a wrong number of arguments it'll raise TypeError,
    #   while Ruby raises ArgumentError
    def initialize(model, sample_rate, grammar_or_spk_model = nil)
      @handle = case grammar_or_spk_model
                when nil
                  C.vosk_recognizer_new(model.handle, sample_rate.to_f)
                when SpkModel
                  C.vosk_recognizer_new_spk(model.handle, sample_rate.to_f, grammar_or_spk_model.handle)
                when String
                  C.vosk_recognizer_new_grm(model.handle, sample_rate.to_f, grammar_or_spk_model)
                else
                  raise TypeError, "Unknown arguments"
                end
    end

    def max_alternatives=(max_alternatives)
      C.vosk_recognizer_set_max_alternatives(@handle, max_alternatives)
    end

    def words=(enable_words)
      C.vosk_recognizer_set_words(@handle, enable_words ? 1 : 0)
    end

    def partial_words=(enable_partial_words)
      C.vosk_recognizer_set_partial_words(@handle, enable_partial_words ? 1 : 0)
    end

    def nlsml=(enable_nlsml)
      C.vosk_recognizer_set_nlsml(@handle, enable_nlsml ? 1 : 0)
    end

    def endpointer_mode=(mode)
      C.vosk_recognizer_set_endpointer_mode(@handle, mode.to_i)
    end

    def set_endpointer_delays(t_start_max, t_end, t_max)
      C.vosk_recognizer_set_endpointer_delays(@handle, t_start_max.to_f, t_end.to_f, t_max.to_f)
    end

    def spk_model=(spk_model)
      C.vosk_recognizer_set_spk_model(@handle, spk_model.handle)
    end

    def grammar=(grammar)
      C.vosk_recognizer_set_grm(@handle, grammar)
    end

    def accept_waveform(data)
      res = C.vosk_recognizer_accept_waveform(@handle, data, data.bytesize)
      raise Error, "Failed to process waveform" if res < 0

      res
    end

    def result
      C.vosk_recognizer_result(@handle)
    end

    def partial_result
      C.vosk_recognizer_partial_result(@handle)
    end

    def final_result
      C.vosk_recognizer_final_result(@handle)
    end

    def reset
      C.vosk_recognizer_reset(@handle)
    end

    # def srt_result(stream, words_per_line: 7)
    #   results = []
    #   while (data = stream.read(4000)) && !data.empty?
    #     results << result if accept_waveform(data).nonzero?
    #   end
    #   results << final_result

    #   subs = []
    #   results.each do |res|
    #     jres = JSON.parse(res)
    #     next unless jres.key?("result")
    #     jres["result"].each_slice(words_per_line) do |line|
    #       index = subs.length + 1
    #       start_time = srt_time(line.first["start"])
    #       end_time = srt_time(line.last["end"])
    #       content = line.map { |w| w["word"] }.join(" ")
    #       subs << "#{index}\n#{start_time} --> #{end_time}\n#{content}\n"
    #     end
    #   end
    #   subs.join("\n")
    # end

    # private

    # def srt_time(seconds)
    #   h = (seconds / 3600).to_i
    #   m = ((seconds % 3600) / 60).to_i
    #   s = (seconds % 60).to_i
    #   ms = ((seconds - seconds.floor) * 1000).round
    #   format("%02d:%02d:%02d,%03d", h, m, s, ms)
    # end
  end

  # Batch model object
  class BatchModel
    attr_reader :handle

    # Python version accepts additional ignored args for some reason
    def initialize(model_path)
      @handle = C.vosk_batch_model_new(model_path)
    end

    def wait
      C.vosk_batch_model_wait(@handle)
    end
  end

  # Batch recognizer object
  class BatchRecognizer
    # Python version accepts *args, but I don't just use regular arguments
    def initialize(batch_model, sample_rate)
      @handle = C.vosk_batch_recognizer_new(batch_model.handle, sample_rate.to_f)
    end

    def accept_waveform(data)
      C.vosk_batch_recognizer_accept_waveform(@handle, data, data.bytesize)
    end

    def result
      res = C.vosk_batch_recognizer_front_result(@handle)
      C.vosk_batch_recognizer_pop(@handle)
      res
    end

    def finish_stream
      C.vosk_batch_recognizer_finish_stream(@handle)
    end

    def pending_chunks
      C.vosk_batch_recognizer_get_pending_chunks(@handle)
    end
  end

  # Inverse text normalization
  class Processor
    # Python version accepts *args, but I don't just use regular arguments
    def initialize(lang, type)
      @handle = C.vosk_text_processor_new(lang, type)
    end

    def process(text)
      C.vosk_text_processor_itn(@handle, text)
    end
  end

  def self.log_level=(level)
    C.vosk_set_log_level(level)
  end

  def self.gpu_init
    C.vosk_gpu_init
  end

  def self.gpu_thread_init
    C.vosk_gpu_thread_init
  end
end
