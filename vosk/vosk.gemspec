# frozen_string_literal: true

require_relative "lib/vosk/version"

Gem::Specification.new do |spec|
  spec.name = "vosk"
  spec.version = Vosk::VERSION
  spec.authors = ["Alpha Cephei Inc", "Vladimir Ulianitsky"]
  spec.email = ["contact@alphacphei.com", "uvlad7@gmail.com"]

  spec.summary = "Offline speech recognition API"
  spec.description =
    "Vosk is an offline open source speech recognition toolkit. " \
    "It enables speech recognition for 20+ languages and dialects - " \
    "English, Indian English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish, Vietnamese, " \
    "Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino, Ukrainian, Kazakh, Swedish, Japanese, " \
    "Esperanto, Hindi, Czech, Polish. More to come."
  spec.homepage = "https://alphacephei.com/vosk"
  spec.license = "Apache-2.0"
  spec.required_ruby_version = ">= 2.5"

  # spec.metadata["allowed_push_host"] = "TODO: Set to your gem server 'https://example.com'"

  spec.metadata["homepage_uri"] = spec.homepage
  spec.metadata["source_code_uri"] = "https://github.com/alphacep/vosk-api"
  # spec.metadata["changelog_uri"] = "TODO: Put your gem's CHANGELOG.md URL here."

  # TODO
  spec.files = [
    *Dir["lib/**/*.rb"],
  ]
  spec.bindir = "exe"
  spec.executables = ["vosk-transcriber"]
  spec.require_paths = ["lib"]

  spec.add_dependency "bytesize", "~> 0.1"
  spec.add_dependency "ffi", "~> 1.6"
  spec.add_dependency "fileutils", "~> 1.7"
  spec.add_dependency "httparty", "~> 0.21"
  spec.add_dependency "progressbar", "~> 1.13"
  spec.add_dependency "rubyzip", "~> 2.4"

  # For more information and examples about making a new gem, check out our
  # guide at: https://bundler.io/guides/creating_gem.html
  spec.metadata["rubygems_mfa_required"] = "true"
end
