package org.vosk

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class Recognizer : PointerType, AutoCloseable {
	actual constructor(model: Model, sampleRate: Float) :
			super(LibVosk.vosk_recognizer_new(model, sampleRate))

	actual constructor(
		model: Model,
		sampleRate: Float,
		speakerModel: SpeakerModel
	) : super(LibVosk.vosk_recognizer_new_spk(model, sampleRate, speakerModel))

	actual constructor(
		model: Model,
		sampleRate: Float,
		grammar: String
	) : super(LibVosk.vosk_recognizer_new_grm(model, sampleRate, grammar))

	actual fun setSpeakerModel(speakerModel: SpeakerModel) {
		LibVosk.vosk_recognizer_set_spk_model(this, speakerModel)
	}

	actual fun setGrammar(grammar: String) {
		LibVosk.vosk_recognizer_set_grm(this, grammar)
	}

	actual fun setMaxAlternatives(maxAlternatives: Int) {
		LibVosk.vosk_recognizer_set_max_alternatives(this, maxAlternatives)
	}

	actual fun setWords(words: Boolean) {
		LibVosk.vosk_recognizer_set_words(this, words)
	}

	actual fun setPartialWords(partialWords: Boolean) {
		LibVosk.vosk_recognizer_set_partial_words(this, partialWords)
	}

	actual fun setNLSML(nlsml: Boolean) {
		LibVosk.vosk_recognizer_set_nlsml(this, nlsml)
	}

	actual fun acceptWaveform(data: ByteArray): Boolean =
		LibVosk.vosk_recognizer_accept_waveform(this, data, data.size)

	actual fun acceptWaveform(data: ShortArray): Boolean =
		LibVosk.vosk_recognizer_accept_waveform_s(this, data, data.size)

	actual fun acceptWaveform(data: FloatArray): Boolean =
		LibVosk.vosk_recognizer_accept_waveform_f(this, data, data.size)


	actual fun result(): String =
		LibVosk.vosk_recognizer_result(this)

	actual fun finalResult(): String =
		LibVosk.vosk_recognizer_final_result(this)

	actual fun partialResult(): String =
		LibVosk.vosk_recognizer_partial_result(this)

	actual fun reset() {
		LibVosk.vosk_recognizer_reset(this)
	}

	actual fun free() {
		LibVosk.vosk_recognizer_free(this)
	}

	override fun close() {
		free()
	}

}