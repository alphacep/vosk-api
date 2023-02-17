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

import cnames.structs.VoskBatchRecognizer
import kotlinx.cinterop.CPointer
import kotlinx.cinterop.toCValues
import kotlinx.cinterop.toKString
import libvosk.*

/**
 * Batch recognizer object
 *
 * 26 / 12 / 2022
 */
actual class BatchRecognizer(val pointer: CPointer<VoskBatchRecognizer>) : Freeable {
	/**
	 * Creates batch recognizer object
	 */
	actual constructor(
		model: BatchModel,
		sampleRate: Float
	) : this(vosk_batch_recognizer_new(model.pointer, sampleRate)!!)

	/**
	 * Releases batch recognizer object
	 */
	actual override fun free() {
		vosk_batch_recognizer_free(pointer)
	}

	/**
	 * Accept batch voice data
	 */
	actual fun acceptWaveform(data: ByteArray) {
		vosk_batch_recognizer_accept_waveform(pointer, data.toCValues(), data.size)
	}

	/**
	 * Set NLSML output
	 * @param nlsml - boolean value
	 */
	actual fun setNLSML(nlsml: Boolean) {
		vosk_batch_recognizer_set_nlsml(pointer, nlsml.toInt())
	}

	/**
	 *  Closes the stream
	 */
	actual fun finishStream() {
		vosk_batch_recognizer_finish_stream(pointer)
	}

	/**
	 * Return results
	 */
	actual val frontResult: String
		get() = vosk_batch_recognizer_front_result(pointer)!!.toKString()

	/**
	 * Release and free first retrieved result
	 */
	actual fun pop() {
		vosk_batch_recognizer_pop(pointer)
	}

	/**
	 * Get amount of pending chunks for more intelligent waiting
	 */
	actual val pendingChunks: Int
		get() = vosk_batch_recognizer_get_pending_chunks(pointer)
}