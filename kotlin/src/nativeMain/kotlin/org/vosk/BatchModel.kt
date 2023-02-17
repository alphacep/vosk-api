/*
 * Copyright 2020 Alpha Cephei Inc. & Doomsdayrs
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

import cnames.structs.VoskBatchModel
import kotlinx.cinterop.CPointer
import libvosk.vosk_batch_model_free
import libvosk.vosk_batch_model_new
import libvosk.vosk_batch_model_wait

/**
 * Batch model object
 *
 * 26 / 12 / 2022
 */
actual class BatchModel(val pointer: CPointer<VoskBatchModel>) : Freeable {
	/**
	 * Creates the batch recognizer object
	 */
	@Throws(IOException::class)
	actual constructor(path: String) : this(vosk_batch_model_new(path) ?: throw ioException(path))

	/**
	 *  Releases batch model object
	 */
	actual override fun free() {
		vosk_batch_model_free(pointer)
	}

	/**
	 * Wait for the processing
	 */
	actual fun await() {
		vosk_batch_model_wait(pointer)
	}
}