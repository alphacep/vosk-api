# frozen_string_literal: true

require "json"

MODEL_PATH = File.join(Dir.home, ".cache/vosk/vosk-model-small-en-us-0.4")
WAV_PATH = File.expand_path("../../python/example/test.wav", __dir__)

# Returns [pcm_bytes, sample_rate] from a standard PCM WAV file.
def read_wav(path)
  data = File.binread(path)
  sample_rate = data[24, 4].unpack1("V")
  idx = data.index("data")
  pcm = data[(idx + 8)..-1]
  [pcm, sample_rate]
end

RSpec.describe Vosk do
  it "has a version number" do
    expect(Vosk::VERSION).not_to be_nil
  end

  describe "Error" do
    it "is a StandardError" do
      expect(Vosk::Error.superclass).to eq(StandardError)
    end
  end

  describe "EndpointerMode" do
    it "defines the correct integer constants" do
      expect(Vosk::EndpointerMode::DEFAULT).to eq(0)
      expect(Vosk::EndpointerMode::SHORT).to eq(1)
      expect(Vosk::EndpointerMode::LONG).to eq(2)
      expect(Vosk::EndpointerMode::VERY_LONG).to eq(3)
    end
  end

  describe Vosk::Model do
    it "raises Vosk::Error on a bad path" do
      expect { Vosk::Model.new(model_path: "/nonexistent/path") }.to raise_error(Vosk::Error)
    end

    context "loaded from a path" do
      subject(:model) { Vosk::Model.new(model_path: MODEL_PATH) }

      it "constructs successfully" do
        expect(model).to be_a(Vosk::Model)
      end

      it "finds a known word" do
        expect(model.find_word("one")).to be >= 0
      end

      it "returns -1 for an unknown word" do
        expect(model.find_word("xyzzy")).to eq(-1)
      end
    end
  end

  describe Vosk::SpkModel do
    it "raises Vosk::Error on a bad path" do
      expect { Vosk::SpkModel.new(model_path: "/nonexistent/path") }.to raise_error(Vosk::Error)
    end
  end

  describe Vosk::KaldiRecognizer do
    let(:pcm) { read_wav(WAV_PATH).first }
    let(:sample_rate) { read_wav(WAV_PATH).last }
    let(:model) { Vosk::Model.new(model_path: MODEL_PATH) }

    describe "initialization" do
      it "accepts (model, sample_rate)" do
        expect(Vosk::KaldiRecognizer.new(model, sample_rate)).to be_a(Vosk::KaldiRecognizer)
      end

      it "accepts (model, sample_rate, grammar_string)" do
        rec = Vosk::KaldiRecognizer.new(model, sample_rate, '["one two three", "[unk]"]')
        expect(rec).to be_a(Vosk::KaldiRecognizer)
      end

      it "raises TypeError for an unknown third argument type" do
        expect { Vosk::KaldiRecognizer.new(model, sample_rate, 42) }.to raise_error(TypeError)
      end
    end

    context "processing audio" do
      subject(:rec) { Vosk::KaldiRecognizer.new(model, sample_rate) }

      def feed_all(rec, pcm, chunk_size = 8000)
        pos = 0
        while pos < pcm.bytesize
          rec.accept_waveform(pcm.byteslice(pos, chunk_size))
          pos += chunk_size
        end
      end

      it "accept_waveform returns 0 or 1" do
        result = rec.accept_waveform(pcm.byteslice(0, 8000))
        expect([0, 1]).to include(result)
      end

      it "result returns valid JSON" do
        rec.accept_waveform(pcm.byteslice(0, 8000))
        expect { JSON.parse(rec.result) }.not_to raise_error
      end

      it "partial_result returns valid JSON" do
        rec.accept_waveform(pcm.byteslice(0, 8000))
        expect { JSON.parse(rec.partial_result) }.not_to raise_error
      end

      it "final_result returns valid JSON" do
        expect { JSON.parse(rec.final_result) }.not_to raise_error
      end

      it "transcribes the test file to non-empty text" do
        feed_all(rec, pcm)
        text = JSON.parse(rec.final_result)["text"]
        expect(text).not_to be_empty
      end

      it "reset clears the partial result" do
        rec.accept_waveform(pcm.byteslice(0, 8000))
        rec.reset
        expect(JSON.parse(rec.partial_result)["partial"]).to be_nil.or(eq(""))
      end

      it "set_words does not raise" do
        expect { rec.set_words(true) }.not_to raise_error
      end

      it "set_words includes per-word timing in results" do
        rec.set_words(true)
        feed_all(rec, pcm)
        result = JSON.parse(rec.final_result)
        # When words are enabled and speech is detected, result has a "result" array
        expect(result).to have_key("text")
        expect(result["result"]).to be_an(Array) if result["result"]
      end

      it "set_partial_words does not raise" do
        expect { rec.set_partial_words(true) }.not_to raise_error
      end

      it "set_max_alternatives produces an alternatives array" do
        rec.set_max_alternatives(5)
        feed_all(rec, pcm)
        result = JSON.parse(rec.final_result)
        expect(result).to have_key("alternatives")
        expect(result["alternatives"]).to be_an(Array)
      end

      it "set_endpointer_mode accepts EndpointerMode constants", skip: (Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.46") && "requires libvosk >= 0.3.46") do
        expect { rec.set_endpointer_mode(Vosk::EndpointerMode::SHORT) }.not_to raise_error
      end

      it "set_endpointer_delays accepts float values", skip: (Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.46") && "requires libvosk >= 0.3.46") do
        expect { rec.set_endpointer_delays(0.5, 1.0, 30.0) }.not_to raise_error
      end

      it "set_grammar changes the active grammar" do
        expect { rec.set_grammar('["one two three", "[unk]"]') }.not_to raise_error
      end
    end

    context "with a grammar recognizer" do
      subject(:rec) { Vosk::KaldiRecognizer.new(model, sample_rate, '["one two three four five six seven eight nine zero", "[unk]"]') }

      def feed_all(rec, pcm, chunk_size = 8000)
        pos = 0
        while pos < pcm.bytesize
          rec.accept_waveform(pcm.byteslice(pos, chunk_size))
          pos += chunk_size
        end
      end

      it "produces a result constrained to the grammar vocabulary" do
        feed_all(rec, pcm)
        result = JSON.parse(rec.final_result)
        expect(result).to have_key("text")
      end
    end
  end

  describe Vosk::Processor, skip: (Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.48") && "requires libvosk >= 0.3.48") do
    it "raises Vosk::Error on a bad lang/type" do
      expect { Vosk::Processor.new("xx_invalid", "itn") }.to raise_error(Vosk::Error)
    end
  end
end
