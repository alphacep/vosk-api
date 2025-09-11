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


/**
 * Batch recognizer object
 *
 * @since 26 / 12 / 2022
 * @constructor Creates batch recognizer object
 */
actual class BatchRecognizer : Freeable, PointerType, AutoCloseable {

	/**
	 * Empty constructor for JNA
	 */
	constructor()

	/**
	 * Creates batch recognizer object
	 */
	actual constructor(model: BatchModel, sampleRate: Float) :
			super(LibVosk.vosk_batch_recognizer_new(model, sampleRate))

	/**
	 * Releases batch recognizer object
	 */
	actual override fun free() {
		LibVosk.vosk_batch_recognizer_free(this);
	}

	/**
	 * Accept batch voice data
	 */
	actual fun acceptWaveform(data: ByteArray) {
		LibVosk.vosk_batch_recognizer_accept_waveform(this, data, data.size)
	}

	/**
	 * Set NLSML output
	 * @param nlsml - boolean value
	 */
	actual fun setNLSML(nlsml: Boolean) {
		LibVosk.vosk_batch_recognizer_set_nlsml(this, nlsml)
	}

	/**
	 *  Closes the stream
	 */
	actual fun finishStream() {
		LibVosk.vosk_batch_recognizer_finish_stream(this)
	}

	/**
	 * Return results
	 */
	actual val frontResult: String
		get() = LibVosk.vosk_batch_recognizer_front_result(this)

	/**
	 * Release and free first retrieved result
	 */
	actual fun pop() {
		LibVosk.vosk_batch_recognizer_pop(this)
	}

	/**
	 * Get amount of pending chunks for more intelligent waiting
	 */
	actual val pendingChunks: Int
		get() = LibVosk.vosk_batch_recognizer_get_pending_chunks(this)

	/**
	 * @see free
	 */
	override fun close() {
		free()
	}
}