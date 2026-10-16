#!/usr/bin/env ruby
# frozen_string_literal: true

# Standalone pre-compiled gem builder. Mirrors Python's setup.py approach.
# Usage: VOSK_SOURCE=... VOSK_SYSTEM=... VOSK_MACHINE=... VOSK_ARCHITECTURE=... ruby build_native_gem.rb
#
# Does not require rake, bundler, rspec, rubocop - only rubygems (stdlib).

require "rubygems"
require "rubygems/package"
require "fileutils"

vosk_source = ENV.fetch("VOSK_SOURCE", File.expand_path("..", __dir__))
vosk_system = ENV.fetch("VOSK_SYSTEM")
vosk_machine = ENV.fetch("VOSK_MACHINE", nil)
vosk_architecture = ENV.fetch("VOSK_ARCHITECTURE", nil)

# Determine gem platform (mirrors Python's get_tag logic)
platform_string = case vosk_system
when "Darwin"
  "universal-darwin"
when "Windows"
  if vosk_machine == "aarch64"
    "arm64-mingw-ucrt"
  elsif vosk_architecture == "32bit"
    "x86-mingw32"
  else
    "x64-mingw32"
  end
when "Linux"
  cpu = case vosk_machine
  when "x86_64"  then "x86_64"
  when "aarch64" then "aarch64"
  when "armv7l"  then "arm"
  when "x86"     then "x86"
  when "riscv64" then "riscv64"
  else raise "Unknown VOSK_MACHINE: #{vosk_machine}"
  end
  "#{cpu}-linux"
else
  raise "Unknown VOSK_SYSTEM: #{vosk_system}"
end

spec = Gem::Specification.load(File.join(__dir__, "vosk.gemspec"))
spec.platform = Gem::Platform.new(platform_string)

# Copy pre-compiled libraries into the gem (same as Python setup.py)
lib_dir = File.join(__dir__, "lib", "vosk")
libs = Dir[File.join(vosk_source, "src", "*.{so,dll,dylib,dyld}")]
libs.each do |lib|
  puts "Adding library #{lib}"
  FileUtils.cp(lib, lib_dir)
end
spec.files += Dir[File.join(__dir__, "lib", "vosk", "*.{so,dll,dylib,dyld}")]
  .map { |f| f.delete_prefix("#{__dir__}/") }

Dir.chdir(__dir__) do
  gem_file = Gem::Package.build(spec)
  FileUtils.mkdir_p("pkg")
  FileUtils.mv(gem_file, "pkg/")
  puts "Created pkg/#{gem_file}"
end
