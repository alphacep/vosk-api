package org.vosk

/**
 * Batch model object
 *
 * 26 / 12 / 2022
 */
expect class BatchModel {

	/**
	 * Creates the batch recognizer object
	 */
	constructor(path: String)

	/**
	 *  Releases batch model object
	 */
	fun free()

	/**
	 * Wait for the processing
	 */
	fun await()
}