package org.vosk

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class BatchRecognizer : PointerType, AutoCloseable {
	actual constructor(model: BatchModel, sampleRate: Float) :
			super(LibVosk.vosk_batch_recognizer_new(model, sampleRate))

	actual fun free() {
		LibVosk.vosk_batch_recognizer_free(this);
	}

	actual fun acceptWaveform(data: ByteArray) {
		LibVosk.vosk_batch_recognizer_accept_waveform(this, data, data.size)
	}

	actual fun setNLSML(nlsml: Boolean) {
		LibVosk.vosk_batch_recognizer_set_nlsml(this, nlsml)
	}

	actual fun finishStream() {
		LibVosk.vosk_batch_recognizer_finish_stream(this)
	}

	actual fun frontResult(): String =
		LibVosk.vosk_batch_recognizer_front_result(this)

	actual fun pop() {
		LibVosk.vosk_batch_recognizer_pop(this)
	}

	actual fun getPendingChunks(): Int =
		LibVosk.vosk_batch_recognizer_get_pending_chunks(this)

	override fun close() {
		free()
	}
}