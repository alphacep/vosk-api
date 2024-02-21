# frozen_string_literal: true

require "vosk"

RSpec.describe Vosk do
  it "has a version number" do
    expect(Vosk::VERSION).to eq("0.3.45")
  end
end
