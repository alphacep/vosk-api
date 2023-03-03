/*
 * Copyright 2023 Alpha Cephei Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.vosk

import com.sun.jna.PointerType
import org.vosk.exception.IOException
import org.vosk.exception.ModelException
import java.io.File
import java.nio.file.Path
import kotlin.io.path.absolutePathString


/**
 * Model stores all the data required for recognition
 *
 * It contains static data and can be shared across processing
 * threads.
 *
 * @since 26 / 12 / 2022
 * @constructor Loads model data from the file and returns the model object
 * @throws IOException if the path provided is invalid
 */
actual class Model : Freeable, PointerType, AutoCloseable {

	/**
	 * Empty constructor for JNA
	 */
	constructor()

	/**
	 * Loads model data from the file and returns the model object
	 */
	@Throws(IOException::class)
	actual constructor(path: String) : super(
		LibVosk.vosk_model_new(path) ?: throw ModelException(path)
	)

	/**
	 * Constructor using a Path, will retrieve absolutePath
	 *
	 * @param path to batch model
	 */
	@Throws(IOException::class)
	constructor(path: Path) : this(path.absolutePathString())

	/**
	 * Constructor using a File, will retrieve absolutePath
	 *
	 * @param file to batch model
	 */
	@Throws(IOException::class)
	constructor(file: File) : this(file.absolutePath)

	/**
	 * Check if a word can be recognized by the model
	 * @param word: the word
	 * @returns the word symbol if @param word exists inside the model
	 * or -1 otherwise.
	 * Reminding that word symbol 0 is for <epsilon>
	 */
	actual fun findWord(word: String): Int =
		LibVosk.vosk_model_find_word(this, word)

	/**
	 * Releases the model memory
	 *
	 *  The model object is reference-counted so if some recognizer
	 *  depends on this model, model might still stay alive. When
	 *  last recognizer is released, model will be released too.
	 */
	actual override fun free() {
		LibVosk.vosk_model_free(this)
	}

	/**
	 * @see free
	 */
	override fun close() {
		free()
	}
}