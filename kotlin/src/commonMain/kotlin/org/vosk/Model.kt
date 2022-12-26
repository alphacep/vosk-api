package org.vosk


/**
 * Model stores all the data required for recognition
 *
 * It contains static data and can be shared across processing
 * threads.
 *
 * 26 / 12 / 2022
 */
expect class Model {
	/**
	 * Loads model data from the file and returns the model object
	 *
	 * @param path: the path of the model on the filesystem
	 * @returns model object or NULL if problem occured
	 */
	constructor(path: String)

	/**
	 * Check if a word can be recognized by the model
	 * @param word: the word
	 * @returns the word symbol if @param word exists inside the model
	 * or -1 otherwise.
	 * Reminding that word symbol 0 is for <epsilon>
	 */
	fun findWord(word: String): Int

	/**
	 * Releases the model memory
	 *
	 *  The model object is reference-counted so if some recognizer
	 *  depends on this model, model might still stay alive. When
	 *  last recognizer is released, model will be released too.
	 */
	fun free()
}