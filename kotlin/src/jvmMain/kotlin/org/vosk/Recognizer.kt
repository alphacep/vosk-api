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

import com.sun.jna.PointerType

/**
 * 26 / 12 / 2022
 */
actual class Recognizer : PointerType, AutoCloseable {
	constructor()
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