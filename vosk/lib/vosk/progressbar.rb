# frozen_string_literal: true

require "progressbar"
require "bytesize"

# Extends progressbar with tqdm-like output:
#   %s / %z  → human-readable byte sizes: current size / total siZe
#   %d / %o  → compact time: elapsed Duration / Outstanding remaining
#   %r       → rate_scale lambda may return a ByteSize string

# Override rate_of_change so rate_scale can return a string.
# The default format '%i' coerces the result to integer, breaking string values.
ProgressBar::Components::Rate.prepend(Module.new do
  def rate_of_change(format_string = "%s")
    return "0" if elapsed_seconds <= 0

    format_string % scaled_rate
  end
end)

# Add ByteSize-formatted progress methods to the Progress component.
class ProgressBar::Progress
  def progress_with_precision
    ByteSize.new(progress).to_s
  end

  def total_with_unknown_indicator_with_precision
    total ? ByteSize.new(total).to_s : total_with_unknown_indicator
  end
end

# Add label-free time methods to the Time component.
class ProgressBar::Components::Time
  def elapsed_no_label
    val = elapsed
    val.start_with?("00:") ? val[3..] : val
  end

  def estimated_no_label
    val = estimated_with_friendly_oob.split(": ", 2).last
    val.start_with?("00:") ? val[3..] : val
  end
end

# Extend MOLECULES with new non-overlapping keys — originals are untouched.
# remove_const avoids the "already initialized constant" warning.
molecules = ProgressBar::Format::Molecule::MOLECULES
ProgressBar::Format::Molecule.send(:remove_const, :MOLECULES)
ProgressBar::Format::Molecule::MOLECULES = molecules.merge(
  s: [:progressable,   :progress_with_precision],
  z: [:progressable,   :total_with_unknown_indicator_with_precision],
  d: [:time_component, :elapsed_no_label],
  o: [:time_component, :estimated_no_label],
).freeze
