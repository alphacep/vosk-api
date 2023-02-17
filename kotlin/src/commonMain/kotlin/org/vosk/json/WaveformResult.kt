package org.vosk.json

/**
 * For extension functions transforming (input streams->recognizers) into flows.
 */
sealed interface WaveformResult {

	/**
	 * A result made after a period of silence.
	 */
	data class Result(val result: ResultOutput) : WaveformResult

	/**
	 * A partial result that is being made in progress.
	 */
	data class PartialResult(val result: PartialResultOutput) : WaveformResult

	/**
	 * A final result made after there is no more content to feed.
	 */
	data class FinalResult(val result: ResultOutput) : WaveformResult
}