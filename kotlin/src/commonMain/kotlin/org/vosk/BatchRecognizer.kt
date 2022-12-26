package org.vosk

/**
 * Batch recognizer object
 *
 * 26 / 12 / 2022
 */
expect class BatchRecognizer {

	/**
	 * Creates batch recognizer object
	 */
	constructor(model: BatchModel, sampleRate: Float)

	/**
	 * Releases batch recognizer object
	 */
	fun free()

	/**
	 * Accept batch voice data
	 */
	fun acceptWaveform(data: ByteArray)

	/**
	 * Set NLSML output
	 * @param nlsml - boolean value
	 */
	fun setNLSML(nlsml: Boolean)

	/**
	 *  Closes the stream
	 */
	fun finishStream()

	/**
	 * Return results
	 */
	fun frontResult(): String

	/**
	 * Release and free first retrieved result
	 */
	fun pop()

	/**
	 * Get amount of pending chunks for more intelligent waiting
	 */
	fun getPendingChunks(): Int
}