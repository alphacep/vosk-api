# Vosk

Ruby bindings to [vosk-api](https://github.com/alphacep/vosk-api) using [fiddle](https://github.com/ruby/fiddle).

## Installation

Add this line to your application's Gemfile:

```ruby
gem 'vosk'
```

Or, to install the gem using `git`:

```ruby
gem "vosk",
  git: "https://github.com/alphacep/vosk-api",
  glob: "ruby/vosk.gemspec"
```

And then execute:

```
bundle install
```

Or install it yourself as:
```
gem install vosk
```

## Usage

```
git clone https://github.com/alphacep/vosk-api
cd vosk-api/ruby
bundle
bundle exec ruby examples/transcribe.rb
```

See [examples/transcribe.rb](examples/transcribe.rb) for more info.

## Development

After checking out the repo, run `bin/setup` to install dependencies. Then, run `rake spec` to run the tests. You can also run `bin/console` for an interactive prompt that will allow you to experiment.

To install this gem onto your local machine, run `bundle exec rake install`. To release a new version, update the version number in `version.rb`, and then run `bundle exec rake release`, which will create a git tag for the version, push git commits and the created tag, and push the `.gem` file to [rubygems.org](https://rubygems.org).

## Contributing

Bug reports and pull requests are welcome on GitHub at https://github.com/alphacep/vosk-api.

## License

The gem is available as open source under the terms of the [Apache-2.0](https://opensource.org/license/apache-2-0/) license.
