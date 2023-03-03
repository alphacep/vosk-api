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

import kotlinx.coroutines.*
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.test.runTest
import org.vosk.*
import java.io.BufferedInputStream
import java.io.FileInputStream
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.sound.sampled.AudioSystem
import javax.sound.sampled.UnsupportedAudioFileException
import kotlin.test.Test

class DecoderTest {
	val modelPath = System.getenv("MODEL")
	val testFile = System.getenv("AUDIO")

	init {
		System.load(System.getenv("LIBRARY"))
		Vosk.setLogLevel(LogLevel.DEBUG)
	}

	@Test
	fun grammarList() {
		Model(modelPath).use { model ->
			Recognizer(model, 16000f, listOf("one")).apply {
				setMaxAlternatives(10)
				setOutputWordTimes(true)
				setPartialWords(true)
			}
		}
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTest() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(model, 16000f).apply {
						setMaxAlternatives(10)
						setOutputWordTimes(true)
						setPartialWords(true)
					}.use { recognizer ->
						val b = ByteArray(4096)
						while (ais.read(b) >= 0) {
							if (recognizer.acceptWaveform(b)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@OptIn(ExperimentalCoroutinesApi::class)
	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestFlow() = runTest {
		Model(modelPath).use { model ->
			Recognizer(model, 16000f).apply {
				setMaxAlternatives(10)
				setOutputWordTimes(true)
				setPartialWords(true)
			}.use { recognizer ->
				AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
					.use { ais ->
						flow {
							val b = ByteArray(4096)
							while (ais.read(b) >= 0) {
								emit(b)
							}
							emit(null)
						}.flowOn(Dispatchers.IO)
							.feed(recognizer)
							.collect {
								println(it)
							}
					}
			}
		}
	}

	/**
	 * This test aims to simulate the situation for Dicio,
	 *  In which we can receive the audio input stream before the recognizer is setup.
	 *
	 *  It is recommended to use a large model on desktop to properly see how long it takes to load up.
	 */
	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestFlowBuffered() {
		// Scope to buffer into
		val scope = CoroutineScope(Dispatchers.IO)

		AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile))).use { ais ->
			val byteFlow = flow {
				val b = ByteArray(4096)
				while (ais.read(b) >= 0) {
					emit(b)
				}
				emit(null)
			}.flowOn(Dispatchers.IO)
				.shareIn(scope, SharingStarted.Eagerly, 100)

			// Tell us the current buffer size
			println("Buffered size:" + byteFlow.replayCache.size)

			var startTime = System.currentTimeMillis()

			Model(modelPath).use { model ->
				var resultTime = System.currentTimeMillis() - startTime
				println("Model initialized in: $resultTime")
				startTime = System.currentTimeMillis()

				Recognizer(model, 16000f).apply {
					setMaxAlternatives(10)
					setOutputWordTimes(true)
					setPartialWords(true)
				}.use { recognizer ->
					resultTime = System.currentTimeMillis() - startTime
					println("Recognizer initialized in: $resultTime")
					println("Buffered size:" + byteFlow.replayCache.size)

					runBlocking {
						byteFlow
							.feed(recognizer)
							.take(byteFlow.replayCache.size)
							.collect {
								println(it)
							}
					}
				}
			}
		}
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestShort() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(model, 16000f).use { recognizer ->
						val b = ByteArray(4096)
						val s = ShortArray(2048)
						while (ais.read(b) >= 0) {
							ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(s)
							if (recognizer.acceptWaveform(s)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestGrammar() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(
						model, 16000f, "[\"one two three four five six seven eight nine zero oh\"]"
					).use { recognizer ->
						val b = ByteArray(4096)
						while (ais.read(b) >= 0) {
							if (recognizer.acceptWaveform(b)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@Test
	fun decoderTestException() {
		try {
			val model = Model("model_missing")
			assert(false)
		} catch (e: IOException) {
			assert(true)
		}
	}
}