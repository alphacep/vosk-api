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

import org.vosk.exception.ModelException

/**
 * Speaker model is the same as model but contains the data
 * for speaker identification.
 *
 * @since 26 / 12 / 2022
 * @constructor Loads speaker model data from the file and returns the model object
 * @param path the path of the model on the filesystem
 * @throws ModelException if the path provided is invalid
 */
expect class SpeakerModel @Throws(ModelException::class) constructor(path: String) : Freeable {

	/**
	 * Releases the model memory
	 *
	 * The model object is reference-counted so if some recognizer
	 * depends on this model, model might still stay alive. When
	 * last recognizer is released, model will be released too.
	 */
	override fun free()
}