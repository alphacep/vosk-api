package org.vosk

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class SpeakerModel : PointerType, AutoCloseable {
	actual constructor(path: String) : super(LibVosk.vosk_spk_model_new(path))

	actual fun free() {
		LibVosk.vosk_spk_model_free(this)
	}

	override fun close() {
		free()
	}

}