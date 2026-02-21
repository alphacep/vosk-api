# frozen_string_literal: true

RSpec.describe Vosk::Model do
  # Allocate an instance without calling initialize — no C library needed.
  let(:model) { described_class.allocate }
  let(:tmpdir) { Dir.mktmpdir }
  let(:model_name) { "vosk-model-small-en-us-0.4" }
  let(:model_list) do
    [{ "name" => model_name, "lang" => "en-us", "type" => "small", "obsolete" => "false" }]
  end

  after { FileUtils.rm_rf(tmpdir) }

  describe "#get_model_by_name" do
    context "when the model directory already exists in MODEL_DIRS" do
      before do
        FileUtils.makedirs(File.join(tmpdir, model_name))
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
      end

      it "returns its path without hitting the network" do
        expect(HTTParty).not_to receive(:get)
        expect(model.send(:get_model_by_name, model_name)).to eq(File.join(tmpdir, model_name))
      end
    end

    context "when the model is not in any MODEL_DIR" do
      before do
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        allow(HTTParty).to receive(:get).with(Vosk::MODEL_LIST_URL, timeout: 10).and_return(model_list)
        allow(model).to receive(:download_model)
      end

      it "downloads the model to the last MODEL_DIR" do
        expect(model).to receive(:download_model).with(File.join(tmpdir, model_name))
        model.send(:get_model_by_name, model_name)
      end

      it "returns the expected path after downloading" do
        expect(model.send(:get_model_by_name, model_name)).to eq(File.join(tmpdir, model_name))
      end

      it "exits when the model name is not in the remote list" do
        expect { model.send(:get_model_by_name, "vosk-model-unknown") }.to raise_error(SystemExit)
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
        expect(HTTParty).not_to receive(:get)
        expect(model.send(:get_model_by_lang, "en-us")).to eq(File.join(tmpdir, model_name))
      end

      it "also matches vosk-model-<lang> (without -small-)" do
        other = "vosk-model-en-us-0.22"
        FileUtils.makedirs(File.join(tmpdir, other))
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        expect(HTTParty).not_to receive(:get)
        expect(model.send(:get_model_by_lang, "en-us")).not_to be_nil
      end
    end

    context "when no local model exists for the language" do
      before do
        stub_const("Vosk::MODEL_DIRS", [tmpdir])
        allow(HTTParty).to receive(:get).with(Vosk::MODEL_LIST_URL, timeout: 10).and_return(model_list)
        allow(model).to receive(:download_model)
      end

      it "downloads a small model for the language" do
        expect(model).to receive(:download_model).with(File.join(tmpdir, model_name))
        model.send(:get_model_by_lang, "en-us")
      end

      it "exits when no model is available for the language" do
        expect { model.send(:get_model_by_lang, "xx-unknown") }.to raise_error(SystemExit)
      end
    end
  end

  describe "#download_model" do
    let(:model_path) { File.join(tmpdir, model_name) }
    let(:source_zip) { File.join(tmpdir, "source.zip") }

    before do
      # Build a zip that mimics the model archive structure.
      Zip::OutputStream.open(source_zip) do |zip|
        zip.put_next_entry("#{model_name}/conf/model.conf")
        zip.write("# model config\n")
        zip.put_next_entry("#{model_name}/README")
        zip.write("test model\n")
      end

      # Suppress progress bar output.
      pb = Struct.new(:progress, :total).new(0, nil)
      pb.define_singleton_method(:finish) {}
      pb.define_singleton_method(:stop) {}
      allow(ProgressBar).to receive(:create).and_return(pb)

      # Stub download_file to deliver the pre-built zip instead of fetching from the network.
      allow(model).to receive(:download_file) do |_url, dest, &callback|
        FileUtils.cp(source_zip, dest)
        callback&.call(File.size(dest), File.size(dest))
      end
    end

    it "extracts the archive into the parent directory" do
      model.send(:download_model, model_path)
      expect(File.exist?(File.join(model_path, "conf/model.conf"))).to be(true)
    end

    it "deletes the zip file after extraction" do
      model.send(:download_model, model_path)
      expect(File.exist?("#{model_path}.zip")).to be(false)
    end

    it "creates the parent directory when it does not yet exist" do
      nested_path = File.join(tmpdir, "new_subdir", model_name)
      model.send(:download_model, nested_path)
      expect(Dir.exist?(File.dirname(nested_path))).to be(true)
    end

    it "uses the correct download URL" do
      expect(model).to receive(:download_file)
        .with("#{Vosk::MODEL_PRE_URL}#{model_name}.zip", anything)
      model.send(:download_model, model_path)
    end
  end
end
