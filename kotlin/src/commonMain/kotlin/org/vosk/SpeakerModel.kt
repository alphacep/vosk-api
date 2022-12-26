package org.vosk

/**
 * Speaker model is the same as model but contains the data
 * for speaker identification.
 *
 * 26 / 12 / 2022
 */
expect class SpeakerModel {
	/**
	 * Loads speaker model data from the file and returns the model object
	 *
	 * @param path: the path of the model on the filesystem
	 * @returns model object or NULL if problem occurred
	 */
	constructor(path: String)

	/**
	 * Releases the model memory
	 *
	 * The model object is reference-counted so if some recognizer
	 * depends on this model, model might still stay alive. When
	 * last recognizer is released, model will be released too.
	 */
	fun free()
}