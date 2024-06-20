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
import org.vosk.exception.ModelException
import java.io.File
import java.nio.file.Path
import kotlin.io.path.absolutePathString


/**
 * Batch model object
 *
 * @since 26 / 12 / 2022
 */
actual class BatchModel : Freeable, PointerType, AutoCloseable {

	/**
	 * Empty constructor for JNA
	 */
	constructor()

	/**
	 * Creates the batch recognizer object
	 */
	@Throws(ModelException::class)
	actual constructor(path: String) : super(
		LibVosk.vosk_batch_model_new(path) ?: throw ModelException(path)
	)

	/**
	 * Constructor using a Path, will retrieve absolutePath
	 *
	 * @param path to batch model
	 */
	@Throws(ModelException::class)
	constructor(path: Path) : this(path.absolutePathString())

	/**
	 * Constructor using a File, will retrieve absolutePath
	 *
	 * @param file to batch model
	 */
	@Throws(ModelException::class)
	constructor(file: File) : this(file.absolutePath)

	/**
	 * Releases batch model object
	 */
	actual override fun free() {
		LibVosk.vosk_batch_model_free(this)
	}

	/**
	 * Wait for the processing
	 */
	actual fun await() {
		LibVosk.vosk_batch_model_wait(this)
	}

	/**
	 * @see free
	 */
	override fun close() {
		free()
	}

}