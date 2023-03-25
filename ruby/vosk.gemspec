# frozen_string_literal: true

require_relative "lib/vosk/version"

Gem::Specification.new do |s|
  s.name        = "vosk"
  s.version     = Vosk::VERSION
  s.summary     = "Offline speech recognition API"
  s.description = "Vosk is an offline open source speech recognition toolkit. It enables speech recognition for 20+ languages and dialects - English, Indian English, German, French, Spanish, Portuguese, Chinese, Russian, Turkish, Vietnamese, Italian, Dutch, Catalan, Arabic, Greek, Farsi, Filipino, Ukrainian, Kazakh, Swedish, Japanese, Esperanto, Hindi, Czech, Polish. More to come." # rubocop:disable Layout/LineLength
  s.authors     = ["Alpha Cephei Inc"]
  s.email       = "contact@alphacphei.com"
  s.files       = Dir.glob("lib/**/*.rb")
  s.homepage    = "https://rubygems.org/gems/vosk"
  s.license = "Apache 2.0"
  s.required_ruby_version = ">= 2.6.0"
  s.metadata["homepage_uri"]          = "https://github.com/alphacep/vosk-api"
  s.metadata["source_code_uri"]       = "https://github.com/alphacep/vosk-api"
  s.metadata["rubygems_mfa_required"] = "true"
end
