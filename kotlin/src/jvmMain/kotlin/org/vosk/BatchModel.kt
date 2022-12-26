package org.vosk

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class BatchModel : PointerType, AutoCloseable {
	actual constructor(path: String) : super(LibVosk.vosk_batch_model_new(path))

	actual fun free() {
		LibVosk.vosk_batch_model_free(this)
	}

	actual fun await() {
		LibVosk.vosk_batch_model_wait(this)
	}

	override fun close() {
		free()
	}

}