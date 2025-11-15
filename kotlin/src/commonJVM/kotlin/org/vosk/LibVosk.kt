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

import com.sun.jna.Native
import com.sun.jna.Platform
import com.sun.jna.Pointer
import java.io.File
import java.io.IOException
import java.io.InputStream
import java.nio.file.Files
import java.nio.file.StandardCopyOption

/**
 * 26 / 12 / 2022
 */
@Suppress("FunctionName")
internal object LibVosk {

	@JvmStatic
	@Deprecated(
		"LibVosk is now for internal JNA, use Vosk instead",
		ReplaceWith("Vosk.setLogLevel(logLevel)", "org.vosk.Vosk")
	)
	fun setLogLevel(logLevel: LogLevel) {
		Vosk.setLogLevel(logLevel)
	}

	@Throws(IOException::class)
	private fun unpackDll(targetDir: File, lib: String) {
		Vosk::class.java.getResourceAsStream("/win32-x86-64/$lib.dll")!!.use {
			Files.copy(
				it,
				File(targetDir, "$lib.dll").toPath(),
				StandardCopyOption.REPLACE_EXISTING
			)
		}
	}

	init {
		when {
			Platform.isAndroid() -> {
				Native.register(LibVosk::class.java, "vosk")
			}

			Platform.isWindows() -> {
				// We have to unpack dependencies
				try {
					// To get a tmp folder we unpack small library and mark it for deletion
					val tmpFile: File = Native.extractFromResourcePath(
						"/win32-x86-64/empty",
						LibVosk::class.java.classLoader
					)
					val tmpDir = tmpFile.parentFile!!
					File(tmpDir, tmpFile.name + ".x").createNewFile()

					// Now unpack dependencies
					unpackDll(tmpDir, "libwinpthread-1");
					unpackDll(tmpDir, "libgcc_s_seh-1");
					unpackDll(tmpDir, "libstdc++-6");

				} catch (e: IOException) {
					// Nothing for now, it will fail on next step
				} finally {
					Native.register(LibVosk::class.java, "libvosk");
				}
			}

			else -> {
				Native.register(LibVosk::class.java, "vosk");
			}
		}
	}


	external fun vosk_model_new(path: String): Pointer?

	external fun vosk_model_free(model: Model)

	external fun vosk_model_find_word(model: Model, word: String): Int


	external fun vosk_spk_model_new(path: String): Pointer?

	external fun vosk_spk_model_free(model: SpeakerModel)


	external fun vosk_recognizer_new(model: Model, sampleRate: Float): Pointer?

	external fun vosk_recognizer_new_spk(
		model: Model,
		sampleRate: Float,
		spkModel: SpeakerModel
	): Pointer?

	external fun vosk_recognizer_new_grm(
		model: Model,
		sampleRate: Float,
		grammar: String?
	): Pointer?

	external fun vosk_recognizer_set_spk_model(recognizer: Recognizer, spk_model: SpeakerModel)

	external fun vosk_recognizer_set_grm(recognizer: Recognizer, grammar: String)

	external fun vosk_recognizer_set_max_alternatives(recognizer: Recognizer, maxAlternatives: Int)

	external fun vosk_recognizer_set_words(recognizer: Recognizer, words: Boolean)

	external fun vosk_recognizer_set_partial_words(recognizer: Recognizer, partial_words: Boolean)

	external fun vosk_recognizer_set_nlsml(recognizer: Recognizer, nlsml: Boolean)


	external fun vosk_recognizer_accept_waveform(
		recognizer: Recognizer,
		data: ByteArray?,
		len: Int
	): Int

	external fun vosk_recognizer_accept_waveform_s(
		recognizer: Recognizer,
		data: ShortArray?,
		len: Int
	): Int

	external fun vosk_recognizer_accept_waveform_f(
		recognizer: Recognizer,
		data: FloatArray?,
		len: Int
	): Int


	external fun vosk_recognizer_result(recognizer: Recognizer): String

	external fun vosk_recognizer_final_result(recognizer: Recognizer): String

	external fun vosk_recognizer_partial_result(recognizer: Recognizer): String


	external fun vosk_recognizer_reset(recognizer: Recognizer)

	external fun vosk_recognizer_free(recognizer: Recognizer)

	external fun vosk_set_log_level(level: Int)

	external fun vosk_gpu_init()

	external fun vosk_gpu_thread_init()


	external fun vosk_batch_model_new(path: String): Pointer?

	external fun vosk_batch_model_free(model: BatchModel)

	external fun vosk_batch_model_wait(model: BatchModel)

	external fun vosk_batch_recognizer_new(batchModel: BatchModel, sampleRate: Float): Pointer

	external fun vosk_batch_recognizer_free(recognizer: BatchRecognizer)

	external fun vosk_batch_recognizer_accept_waveform(
		recognizer: BatchRecognizer,
		data: ByteArray?,
		length: Int
	)

	external fun vosk_batch_recognizer_set_nlsml(
		recognizer: BatchRecognizer,
		nlsml: Boolean
	)

	external fun vosk_batch_recognizer_finish_stream(
		recognizer: BatchRecognizer
	)

	external fun vosk_batch_recognizer_front_result(
		recognizer: BatchRecognizer
	): String

	external fun vosk_batch_recognizer_pop(recognizer: BatchRecognizer)

	external fun vosk_batch_recognizer_get_pending_chunks(recognizer: BatchRecognizer): Int

	external fun vosk_text_processor_new(tagger: Char, verbalizer: Char): Pointer

	external fun vosk_text_processor_free(processor: TextProcessor)

	external fun vosk_text_processor_itn(processor: TextProcessor, input: Char): Char

	external fun vosk_recognizer_set_endpointer_mode(recognizer: Recognizer, ordinal: Int)

	external fun vosk_recognizer_set_endpointer_delays(
		recognizer: Recognizer,
		tStartMax: Float,
		tEnd: Float,
		tMax: Float
	)
}