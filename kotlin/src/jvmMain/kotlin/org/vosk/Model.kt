package org.vosk

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class Model : PointerType, AutoCloseable {
	actual constructor(path: String) : super(LibVosk.vosk_model_new(path))

	actual fun findWord(word: String): Int =
		LibVosk.vosk_model_find_word(this, word)

	actual fun free() {
		LibVosk.vosk_model_free(this)
	}

	override fun close() {
		free()
	}
}