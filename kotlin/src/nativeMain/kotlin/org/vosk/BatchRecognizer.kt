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
actual class BatchRecognizer(val pointer: CPointer<VoskBatchRecognizer>) {
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
	actual fun free() {
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
	actual fun frontResult(): String =
		vosk_batch_recognizer_front_result(pointer)!!.toKString()

	/**
	 * Release and free first retrieved result
	 */
	actual fun pop() {
		vosk_batch_recognizer_pop(pointer)
	}

	/**
	 * Get amount of pending chunks for more intelligent waiting
	 */
	actual fun getPendingChunks(): Int =
		vosk_batch_recognizer_get_pending_chunks(pointer)
}