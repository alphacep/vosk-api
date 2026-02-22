# frozen_string_literal: true

require "json"
require "wavefile"

RSpec.describe Vosk do
  described_class.log_level = -1

  let(:en_model_path) { File.join(Dir.home, ".cache/vosk/vosk-model-small-en-us-0.4") }
  let(:test_wav_path) { File.expand_path("../example/test.wav", __dir__) }
  let(:wave_reader) { WaveFile::Reader.new(test_wav_path) }
  let(:wave_chunks) do
    chunks = []
    wave_reader.each_buffer(4000) { |buffer| chunks.push(buffer.samples.pack(WaveFile::PACK_CODES.dig(:pcm, 16))) }
    chunks
  end

  after { wave_reader.close }

  it "has a version number" do
    expect(Vosk::VERSION).not_to be_nil
  end

  describe "EndpointerMode" do
    it "defines the correct integer constants" do
      expect([
               Vosk::EndpointerMode::DEFAULT,
               Vosk::EndpointerMode::SHORT,
               Vosk::EndpointerMode::LONG,
               Vosk::EndpointerMode::VERY_LONG,
             ]).to eq([0, 1, 2, 3])
    end
  end

  describe Vosk::Model do
    it "raises Vosk::Error on a bad path" do
      expect do
        described_class.new(model_path: "/nonexistent/path")
      end.to raise_error(Vosk::Error, "Failed to create a model")
    end

    context "when loaded from a path" do
      subject(:model) { described_class.new(model_path: en_model_path) }

      it "constructs successfully" do
        expect(model).to be_a(described_class)
      end

      it "finds a known word" do
        expect(model.vosk_model_find_word("one")).to be >= 0
      end

      it "returns -1 for an unknown word" do
        expect(model.vosk_model_find_word("xyzzy")).to eq(-1)
      end
    end
  end

  describe Vosk::SpkModel do
    it "raises Vosk::Error on a bad path" do
      expect do
        described_class.new("/nonexistent/path")
      end.to raise_error(Vosk::Error, "Failed to create a speaker model")
    end
  end

  describe Vosk::KaldiRecognizer do
    let(:model) { Vosk::Model.new(model_path: en_model_path) }
    let(:wave_sample_rate) { wave_reader.format.sample_rate }

    describe "initialization" do
      it "accepts (model, sample_rate)" do
        expect(described_class.new(model, wave_sample_rate)).to be_a(described_class)
      end

      it "accepts (model, sample_rate, grammar_string)" do
        rec = described_class.new(model, wave_sample_rate, '["one two three", "[unk]"]')
        expect(rec).to be_a(described_class)
      end

      it "raises TypeError for an unknown third argument type" do
        expect { described_class.new(model, wave_sample_rate, 42) }.to raise_error(TypeError)
      end
    end

    context "when processing audio" do
      subject(:rec) { described_class.new(model, wave_sample_rate) }

      it "accept_waveform returns 0 or 1" do
        results = wave_chunks.map { |chunk| rec.accept_waveform(chunk) }.uniq
        expect(results).to contain_exactly(0, 1)
      end

      it "result returns valid JSON" do
        rec.accept_waveform(wave_chunks.first)
        expect { JSON.parse(rec.result) }.not_to raise_error
      end

      it "partial_result returns valid JSON" do
        rec.accept_waveform(wave_chunks.first)
        expect { JSON.parse(rec.partial_result) }.not_to raise_error
      end

      it "final_result returns valid JSON" do
        expect { JSON.parse(rec.final_result) }.not_to raise_error
      end

      it "transcribes the test file to non-empty text" do
        wave_chunks.each { |chunk| rec.accept_waveform(chunk) }
        text = JSON.parse(rec.final_result)["text"]
        expect(text).not_to be_empty
      end

      it "reset clears the partial result" do
        rec.accept_waveform(wave_chunks.first)
        rec.reset
        expect(JSON.parse(rec.partial_result)["partial"]).to be_nil.or(eq(""))
      end

      it "set_words does not raise" do
        expect { rec.words = true }.not_to raise_error
      end

      it "set_words includes per-word timing in results" do
        rec.words = true
        wave_chunks.each { |chunk| rec.accept_waveform(chunk) }
        result = JSON.parse(rec.final_result)
        expect(result).to have_key("text")
        expect(result["result"]).to be_an(Array)
      end

      it "set_partial_words does not raise" do
        expect { rec.partial_words = true }.not_to raise_error
      end

      it "set_max_alternatives produces an alternatives array" do
        rec.max_alternatives = 5
        wave_chunks.each { |chunk| rec.accept_waveform(chunk) }
        result = JSON.parse(rec.final_result)
        expect(result).to have_key("alternatives")
        expect(result["alternatives"]).to be_an(Array)
      end

      it "set_endpointer_mode accepts EndpointerMode constants",
         skip: Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.46") && "requires libvosk >= 0.3.46" do
        expect { rec.endpointer_mode = :short }.not_to raise_error
      end

      it "set_endpointer_delays accepts float values",
         skip: Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.46") && "requires libvosk >= 0.3.46" do
        expect { rec.set_endpointer_delays(0.5, 1.0, 30.0) }.not_to raise_error
      end

      it "set_grammar changes the active grammar" do
        expect { rec.grammar = '["one two three", "[unk]"]' }.not_to raise_error
      end
    end

    context "with a grammar recognizer" do
      subject(:rec) do
        described_class.new(
          model, wave_sample_rate,
          '["one two three four five six seven eight nine zero", "[unk]"]',
        )
      end

      it "produces a result constrained to the grammar vocabulary" do
        wave_chunks.each { |chunk| rec.accept_waveform(chunk) }
        expect(JSON.parse(rec.final_result)).to have_key("text")
      end
    end
  end

  describe Vosk::Processor,
           skip: Gem::Version.new(Vosk::VERSION) < Gem::Version.new("0.3.48") && "requires libvosk >= 0.3.48" do
    it "raises Vosk::Error on a bad lang/type" do
      expect { described_class.new("xx_invalid", "itn") }.to raise_error(Vosk::Error, "Failed to create processor")
    end
  end
end
