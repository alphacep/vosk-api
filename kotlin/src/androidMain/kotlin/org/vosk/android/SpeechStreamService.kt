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
package org.vosk.android

import android.os.Handler
import android.os.Looper
import org.vosk.Recognizer
import java.io.IOException
import java.io.InputStream
import kotlin.math.roundToInt

/**
 * Service that recognizes stream audio in a  thread, passes it to a recognizer and emits
 * recognition results. Recognition events are passed to a client using
 * [RecognitionListener]
 */
class SpeechStreamService(
	private val recognizer: Recognizer,
	inputStream: InputStream,
	sampleRate: Float
) {
	private val inputStream: InputStream
	private val sampleRate: Int
	private val bufferSize: Int
	private var recognizerThread: Thread? = null
	private val mainHandler = Handler(Looper.getMainLooper())

	/**
	 * Creates speech service.
	 */
	init {
		this.sampleRate = sampleRate.toInt()
		this.inputStream = inputStream
		bufferSize = (this.sampleRate * BUFFER_SIZE_SECONDS * 2).roundToInt()
	}

	/**
	 * Starts recognition. Does nothing if recognition is active.
	 *
	 * @return true if recognition was actually started
	 */
	fun start(listener: RecognitionListener): Boolean {
		if (null != recognizerThread) return false
		recognizerThread = RecognizerThread(listener)
		recognizerThread!!.start()
		return true
	}

	/**
	 * Starts recognition. After specified timeout listening stops and the
	 * endOfSpeech signals about that. Does nothing if recognition is active.
	 *
	 *
	 * timeout - timeout in milliseconds to listen.
	 *
	 * @return true if recognition was actually started
	 */
	fun start(listener: RecognitionListener, timeout: Int): Boolean {
		if (null != recognizerThread) return false
		recognizerThread = RecognizerThread(listener, timeout)
		recognizerThread!!.start()
		return true
	}

	/**
	 * Stops recognition. All listeners should receive final result if there is
	 * any. Does nothing if recognition is not active.
	 *
	 * @return true if recognition was actually stopped
	 */
	fun stop(): Boolean {
		if (null == recognizerThread) return false
		try {
			recognizerThread!!.interrupt()
			recognizerThread!!.join()
		} catch (e: InterruptedException) {
			// Restore the interrupted status.
			Thread.currentThread().interrupt()
		}
		recognizerThread = null
		return true
	}

	private inner class RecognizerThread @JvmOverloads constructor(
		var listener: RecognitionListener,
		timeout: Int = Companion.NO_TIMEOUT
	) : Thread() {
		private var remainingSamples: Int
		private val timeoutSamples: Int

		init {
			if (timeout != Companion.NO_TIMEOUT) timeoutSamples =
				timeout * sampleRate / 1000 else timeoutSamples = Companion.NO_TIMEOUT
			remainingSamples = timeoutSamples
		}

		override fun run() {
			val buffer = ByteArray(bufferSize)
			while (!interrupted()
				&& (timeoutSamples == Companion.NO_TIMEOUT || remainingSamples > 0)
			) {
				try {
					val nread = inputStream.read(buffer, 0, buffer.size)
					if (nread < 0) {
						break
					} else {
						val isSilence: Boolean = recognizer.acceptWaveform(buffer)
						if (isSilence) {
							val result = recognizer.result
							mainHandler.post { listener.onResult(result) }
						} else {
							val partialResult = recognizer.partialResult
							mainHandler.post { listener.onPartialResult(partialResult) }
						}
					}
					if (timeoutSamples != NO_TIMEOUT) {
						remainingSamples -= nread
					}
				} catch (e: IOException) {
					mainHandler.post { listener.onError(e) }
				}
			}

			// If we met timeout signal that speech ended
			if (timeoutSamples != NO_TIMEOUT && remainingSamples <= 0) {
				mainHandler.post { listener.onTimeout() }
			} else {
				val finalResult = recognizer.finalResult
				mainHandler.post { listener.onFinalResult(finalResult) }
			}
		}
	}

	companion object {
		private const val NO_TIMEOUT = -1
		private const val BUFFER_SIZE_SECONDS = 0.2f
	}
}