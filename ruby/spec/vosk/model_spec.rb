# frozen_string_literal: true

RSpec.describe Vosk::Model do
  let(:tmpdir) { Dir.mktmpdir }
  let(:en_model_path) { File.join(Dir.home, ".cache/vosk/vosk-model-small-en-us-0.4") }
  let(:model_name) { "vosk-model-small-en-us-0.4" }
  let(:model_list) do
    [{ "name" => model_name, "lang" => "en-us", "type" => "small", "obsolete" => "false" }]
  end
  # Allocate an instance without calling initialize — no C library needed.
  let(:stub_model) { described_class.allocate }

  after { FileUtils.rm_rf(tmpdir) }

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

  describe "#get_model_by_name" do
    context "when the model directory already exists in MODEL_DIRS" do
      before do
        FileUtils.makedirs(File.join(tmpdir, model_name))
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
      end

      it "returns its path without hitting the network" do
        expect(stub_model.send(:get_model_by_name, model_name)).to eq(File.join(tmpdir, model_name))
      end
    end

    context "when the model is not in any MODEL_DIR" do
      before do
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        stub_request(:get, Vosk::MODEL_LIST_URL)
          .to_return(status: 200, body: model_list.to_json, headers: { "Content-Type" => "application/json" })
        allow(stub_model).to receive(:download_model)
      end

      it "downloads the model to the last MODEL_DIR" do
        stub_model.send(:get_model_by_name, model_name)
        expect(stub_model).to have_received(:download_model).with(File.join(tmpdir, model_name))
      end

      it "returns the expected path after downloading" do
        expect(stub_model.send(:get_model_by_name, model_name)).to eq(File.join(tmpdir, model_name))
      end

      it "exits when the model name is not in the remote list" do
        expect { stub_model.send(:get_model_by_name, "vosk-model-unknown") }.to raise_error(SystemExit)
      end
    end
  end

  describe "#get_model_by_lang" do
    context "when a matching model directory already exists" do
      before do
        FileUtils.makedirs(File.join(tmpdir, model_name))
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
      end

      it "returns its path without hitting the network" do
        expect(stub_model.send(:get_model_by_lang, "en-us")).to eq(File.join(tmpdir, model_name))
      end

      it "also matches vosk-model-<lang> (without -small-)" do
        other = "vosk-model-en-us-0.22"
        FileUtils.makedirs(File.join(tmpdir, other))
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        expect(stub_model.send(:get_model_by_lang, "en-us")).not_to be_nil
      end
    end

    context "when no local model exists for the language" do
      before do
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        stub_request(:get, Vosk::MODEL_LIST_URL)
          .to_return(status: 200, body: model_list.to_json, headers: { "Content-Type" => "application/json" })
        allow(stub_model).to receive(:download_model)
      end

      it "downloads a small model for the language" do
        stub_model.send(:get_model_by_lang, "en-us")
        expect(stub_model).to have_received(:download_model).with(File.join(tmpdir, model_name))
      end

      it "exits when no model is available for the language" do
        expect { stub_model.send(:get_model_by_lang, "xx-unknown") }.to raise_error(SystemExit)
      end
    end
  end

  describe "#download_model" do
    let(:model_path) { File.join(tmpdir, model_name) }
    let(:zip_content) do
      Zip::OutputStream.write_buffer do |zip|
        zip.put_next_entry("#{model_name}/conf/model.conf")
        zip.write("# model config\n" * 1_000)
        zip.put_next_entry("#{model_name}/README")
        zip.write("test model\n")
      end.string
    end
    let(:progress_bar_content) { StringIO.new }
    let(:progress_bar_stream) do
      dbl = double
      allow(dbl).to receive(:tty?).with(no_args).and_return(true)
      allow(dbl).to receive(:print) do |*args|
        progress_bar_content.print(*args)
      end
      allow(dbl).to receive(:flush).with(no_args).and_return(dbl)
      allow(dbl).to receive(:winsize).with(no_args).and_return([40, 180])
      dbl
    end

    before do
      stub_const("ProgressBar::Output::DEFAULT_OUTPUT_STREAM", progress_bar_stream)
      stub_request(:get, "#{Vosk::MODEL_PRE_URL}#{model_name}.zip")
        .to_return(status: 200, body: zip_content, headers: { "Content-Length" => zip_content.bytesize.to_s })
    end

    it "extracts the archive into the parent directory" do
      stub_model.send(:download_model, model_path)
      expect(File.exist?(File.join(model_path, "conf/model.conf"))).to be(true)
    end

    it "deletes the zip file after extraction" do
      stub_model.send(:download_model, model_path)
      expect(File.exist?("#{model_path}.zip")).to be(false)
    end

    it "creates the parent directory when it does not yet exist" do
      nested_path = File.join(tmpdir, "new_subdir", model_name)
      stub_model.send(:download_model, nested_path)
      expect(Dir.exist?(File.dirname(nested_path))).to be(true)
    end

    it "uses the correct download URL" do
      stub_model.send(:download_model, model_path)
      expect(WebMock).to have_requested(:get, "#{Vosk::MODEL_PRE_URL}#{model_name}.zip")
    end

    it "displays a progress bar during download" do
      stub_model.send(:download_model, model_path)
      # TODO: test callback when multiple fragments are received
      expect(progress_bar_content.string).to eq(
        (" " * 180).concat(
          "\r" \
          "vosk-model-small-en-us-0.4.zip:   0%|=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=---=--" \
          "-=---=---=---=---=---=---=---=---=---=---=| 0 bytes/?? [00:00<??:??:??, 0/s]\r" \
          "vosk-model-small-en-us-0.4.zip: 100%|███████████████████████████████████████████████████████████████████" \
          "████████████████████████████████████| 402 bytes/402 bytes [00:00<00:00, 0/s]\n",
        ),
      )
    end
  end
end
