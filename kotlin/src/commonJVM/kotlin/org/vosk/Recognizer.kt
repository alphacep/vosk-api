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
import org.vosk.exception.RecognizerException

/**
 * Recognizer object is the main object which processes data.
 *
 * Each recognizer usually runs in own thread and takes audio as input.
 * Once audio is processed recognizer returns JSON object as a string
 * which represent decoded information - words, confidences, times, n-best lists,
 * speaker information and so on
 *
 * @since 26 / 12 / 2022
 */
actual class Recognizer : Freeable, PointerType, AutoCloseable {

	/**
	 * Empty constructor for JNA
	 */
	constructor()

	/**
	 * Creates the recognizer object
	 *
	 *  The recognizers process the speech and return text using shared model data
	 *  @param model       VoskModel containing static data for recognizer. Model can be
	 *                     shared across recognizers, even running in different threads.
	 *  @param sampleRate The sample rate of the audio you going to feed into the recognizer.
	 *                     Make sure this rate matches the audio content, it is a common
	 *                     issue causing accuracy problems.
	 * @throws RecognizerException if a problem occurred
	 */
	@Throws(RecognizerException::class)
	actual constructor(model: Model, sampleRate: Float) :
			super(LibVosk.vosk_recognizer_new(model, sampleRate) ?: throw RecognizerException())

	/**
	 * Creates the recognizer object with speaker recognition
	 *
	 *  With the speaker recognition mode the recognizer not just recognize
	 *  text but also return speaker vectors one can use for speaker identification
	 *
	 *  @param model       VoskModel containing static data for recognizer. Model can be
	 *                     shared across recognizers, even running in different threads.
	 *  @param sampleRate The sample rate of the audio you going to feed into the recognizer.
	 *                     Make sure this rate matches the audio content, it is a common
	 *                     issue causing accuracy problems.
	 *  @param speakerModel speaker model for speaker identification
	 * @throws RecognizerException if a problem occurred
	 */
	@Throws(RecognizerException::class)
	actual constructor(
		model: Model,
		sampleRate: Float,
		speakerModel: SpeakerModel
	) : super(
		LibVosk.vosk_recognizer_new_spk(model, sampleRate, speakerModel)
			?: throw RecognizerException()
	)

	/**
	 * Creates the recognizer object with the phrase list
	 *
	 *  Sometimes when you want to improve recognition accuracy and when you don't need
	 *  to recognize large vocabulary you can specify a list of phrases to recognize. This
	 *  will improve recognizer speed and accuracy but might return [unk] if user said
	 *  something different.
	 *
	 *  Only recognizers with lookahead models support this type of quick configuration.
	 *  Precompiled HCLG graph models are not supported.
	 *
	 *  @param model       VoskModel containing static data for recognizer. Model can be
	 *                     shared across recognizers, even running in different threads.
	 *  @param sampleRate The valuesample rate of the audio you going to feed into the recognizer.
	 *                     Make sure this rate matches the audio content, it is a common
	 *                     issue causing accuracy problems.
	 *  @param grammar The string with the list of phrases to recognize as JSON array of strings,
	 *                 for example "["one two three four five", "[unk]"]".
	 *
	 * @throws RecognizerException if a problem occurred
	 */
	@Throws(RecognizerException::class)
	actual constructor(
		model: Model,
		sampleRate: Float,
		grammar: String
	) : super(
		LibVosk.vosk_recognizer_new_grm(model, sampleRate, grammar) ?: throw RecognizerException()
	)

	/**
	 * JVM analog of Kotlin extension
	 * @see [org.vosk.json.Recognizer]
	 */
	@Throws(RecognizerException::class)
	constructor(
		model: Model,
		sampleRate: Float,
		grammar: List<String>
	) : super(
		// We need the full qualifer to avoid any build issues
		@Suppress("RemoveRedundantQualifierName")
		org.vosk.json.Recognizer(model, sampleRate, grammar).pointer
	)

	/**
	 * Adds speaker model to already initialized recognizer
	 *
	 * Can add speaker recognition model to already created recognizer. Helps to initialize
	 * speaker recognition for grammar-based recognizer.
	 *
	 * @param speakerModel Speaker recognition model
	 */
	actual fun setSpeakerModel(speakerModel: SpeakerModel) {
		LibVosk.vosk_recognizer_set_spk_model(this, speakerModel)
	}

	/**
	 * Reconfigures recognizer to use grammar
	 *
	 * @param grammar      Set of phrases in JSON array of strings or "[]" to use default model graph.
	 *                     See also vosk_recognizer_new_grm
	 */
	actual fun setGrammar(grammar: String) {
		LibVosk.vosk_recognizer_set_grm(this, grammar)
	}

	/**
	 * Configures recognizer to output n-best results
	 *
	 * <pre>
	 *   {
	 *      "alternatives": [
	 *          { "text": "one two three four five", "confidence": 0.97 },
	 *          { "text": "one two three for five", "confidence": 0.03 },
	 *      ]
	 *   }
	 * </pre>
	 *
	 * @param maxAlternatives - maximum alternatives to return from recognition results
	 */
	actual fun setMaxAlternatives(maxAlternatives: Int) {
		LibVosk.vosk_recognizer_set_max_alternatives(this, maxAlternatives)
	}

	/**
	 * Enables words with times in the output
	 *
	 * <pre>
	 *   "result" : [{
	 *       "conf" : 1.000000,
	 *       "end" : 1.110000,
	 *       "start" : 0.870000,
	 *       "word" : "what"
	 *     }, {
	 *       "conf" : 1.000000,
	 *       "end" : 1.530000,
	 *       "start" : 1.110000,
	 *       "word" : "zero"
	 *     }, {
	 *       "conf" : 1.000000,
	 *       "end" : 1.950000,
	 *       "start" : 1.530000,
	 *       "word" : "zero"
	 *     }, {
	 *       "conf" : 1.000000,
	 *       "end" : 2.340000,
	 *       "start" : 1.950000,
	 *       "word" : "zero"
	 *     }, {
	 *       "conf" : 1.000000,
	 *       "end" : 2.610000,
	 *       "start" : 2.340000,
	 *       "word" : "one"
	 *     }],
	 * </pre>
	 *
	 * @param words - boolean value
	 */
	actual fun setOutputWordTimes(words: Boolean) {
		LibVosk.vosk_recognizer_set_words(this, words)
	}

	/**
	 * Like [setOutputWordTimes] return words and confidences in partial results
	 *
	 * @param partialWords - boolean value
	 */
	actual fun setPartialWords(partialWords: Boolean) {
		LibVosk.vosk_recognizer_set_partial_words(this, partialWords)
	}

	/**
	 * Set NLSML output
	 * @param nlsml - boolean value
	 */
	actual fun setNLSML(nlsml: Boolean) {
		LibVosk.vosk_recognizer_set_nlsml(this, nlsml)
	}

	/**
	 * Accept voice data
	 *
	 *  accept and process new chunk of voice data
	 *
	 *  @param data Audio data in PCM 16-bit mono format.
	 *  @param length Length of the audio data.
	 *  @returns
	 *       1 - If silence is occurred and you can retrieve a new utterance with result method
	 *       0 - If decoding continues
	 *      -1 - If exception occurred
	 */
	@Throws(AcceptWaveformException::class)
	actual fun acceptWaveform(data: ByteArray): Boolean {
		val result = LibVosk.vosk_recognizer_accept_waveform(this, data, data.size)
		if (result == -1) throw AcceptWaveformException(data)
		return result == 1
	}

	/**
	 * Same as [acceptWaveform] but the version with the short data for language bindings where you have
	 *  audio as array of shorts
	 */
	@Throws(AcceptWaveformException::class)
	actual fun acceptWaveform(data: ShortArray): Boolean {
		val result = LibVosk.vosk_recognizer_accept_waveform_s(this, data, data.size)
		if (result == -1) throw AcceptWaveformException(data)
		return result == 1
	}

	/**
	 * Same as [acceptWaveform] but the version with the float data for language bindings where you have
	 *  audio as array of floats
	 */
	@Throws(AcceptWaveformException::class)
	actual fun acceptWaveform(data: FloatArray): Boolean {
		val result = LibVosk.vosk_recognizer_accept_waveform_f(this, data, data.size)
		if (result == -1) throw AcceptWaveformException(data)
		return result == 1
	}


	/**
	 * Returns speech recognition result
	 *
	 * @returns the result in JSON format which contains decoded line, decoded
	 *          words, times in seconds and confidences. You can parse this result
	 *          with any json parser
	 *
	 * <pre>
	 *  {
	 *    "text" : "what zero zero zero one"
	 *  }
	 * </pre>
	 *
	 * If alternatives enabled it returns result with alternatives, see also [setMaxAlternatives].
	 *
	 * If word times enabled returns word time, see also [setOutputWordTimes].
	 */
	actual val result: String
		get() = LibVosk.vosk_recognizer_result(this)

	/**
	 * Returns partial speech recognition
	 *
	 * @returns partial speech recognition text which is not yet finalized.
	 *          result may change as recognizer process more data.
	 *
	 * <pre>
	 * {
	 *    "partial" : "cyril one eight zero"
	 * }
	 * </pre>
	 */
	actual val finalResult: String
		get() = LibVosk.vosk_recognizer_final_result(this)

	/**
	 * Returns speech recognition result. Same as result, but doesn't wait for silence
	 *  You usually call it in the end of the stream to get final bits of audio. It
	 *  flushes the feature pipeline, so all remaining audio chunks got processed.
	 *
	 *  @returns speech result in JSON format.
	 */
	actual val partialResult: String
		get() = LibVosk.vosk_recognizer_partial_result(this)

	/**
	 * Resets the recognizer
	 *
	 *  Resets current results so the recognition can continue from scratch
	 */
	actual fun reset() {
		LibVosk.vosk_recognizer_reset(this)
	}

	/**
	 * Releases recognizer object
	 *
	 *  Underlying model is also unreferenced and if needed released
	 */
	actual override fun free() {
		LibVosk.vosk_recognizer_free(this)
	}

	/**
	 * @see free
	 */
	override fun close() {
		free()
	}

	/**
	 * Set endpointer scaling factor
	 *
	 * @param mode Endpointer mode
	 **/
	actual fun setEndPointerMode(mode: EndPointerMode) {
		LibVosk.vosk_recognizer_set_endpointer_mode(this, mode.ordinal)
	}

	/**
	 * Set endpointer delays
	 *
	 * @param tStartMax timeout for stopping recognition in case of initial silence (usually around 5.0)
	 * @param tEnd      timeout for stopping recognition in milliseconds after we recognized something (usually around 0.5 - 1.0)
	 * @param tMax      timeout for forcing utterance end in milliseconds (usually around 20-30)
	 **/
	actual fun setEndPointerDelays(
		tStartMax: Float,
		tEnd: Float,
		tMax: Float
	) {
		LibVosk.vosk_recognizer_set_endpointer_delays(this, tStartMax, tEnd, tMax)
	}
}