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

import android.annotation.SuppressLint
import android.media.AudioFormat
import android.media.AudioRecord
import android.media.MediaRecorder.AudioSource
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import org.vosk.Recognizer
import java.io.IOException
import kotlin.math.roundToInt

/**
 * Service that records audio in a thread, passes it to a recognizer and emits
 * recognition results. Recognition events are passed to a client using
 * [RecognitionListener]
 */
class SpeechService @Throws(IOException::class) constructor(
	private val recognizer: Recognizer,
	sampleRate: Float
) {
	private val sampleRate: Int
	private val bufferSize: Int
	private val recorder: AudioRecord

	private val scope = CoroutineScope(Dispatchers.IO)
	private var recognizerThread: Job? = null

	private var paused = false
	private var reset = false
	private var interrupt = false

	/**
	 * Creates speech service. Service holds the AudioRecord object, so you
	 * need to call [.shutdown] in order to properly finalize it.
	 *
	 * @throws IOException thrown if audio recorder can not be created for some reason.
	 */
	init {
		this.sampleRate = sampleRate.toInt()
		bufferSize = (this.sampleRate * BUFFER_SIZE_SECONDS).roundToInt()
		@SuppressLint("MissingPermission")
		recorder = AudioRecord(
			AudioSource.VOICE_RECOGNITION, this.sampleRate,
			AudioFormat.CHANNEL_IN_MONO,
			AudioFormat.ENCODING_PCM_16BIT, bufferSize * 2
		)
		if (recorder.state == AudioRecord.STATE_UNINITIALIZED) {
			recorder.release()
			throw IOException(
				"Failed to initialize recorder. Microphone might be already in use."
			)
		}
	}

	/**
	 * Starts recognition. Does nothing if recognition is active.
	 *
	 * @return true if recognition was actually started
	 */
	fun startListening(listener: RecognitionListener): Boolean {
		if (null != recognizerThread) return false
		recognizerThread = scope.launch { startRecognizer(listener) }
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
	fun startListening(listener: RecognitionListener, timeout: Int): Boolean {
		if (null != recognizerThread) return false
		recognizerThread = scope.launch { startRecognizer(listener, timeout) }
		return true
	}

	private suspend fun stopRecognizerThread(): Boolean {
		if (null == recognizerThread) return false
		try {
			interrupt = true
			recognizerThread!!.join()
		} catch (e: InterruptedException) {
			// Restore the interrupted status.
			Thread.currentThread().interrupt()
		}
		recognizerThread = null
		interrupt = false
		return true
	}

	/**
	 * Stops recognition. Listener should receive final result if there is
	 * any. Does nothing if recognition is not active.
	 *
	 * @return true if recognition was actually stopped
	 */
	fun stop(): Boolean {
		return runBlocking { stopRecognizerThread() }
	}

	/**
	 * Cancel recognition. Do not post any new events, simply cancel processing.
	 * Does nothing if recognition is not active.
	 *
	 * @return true if recognition was actually stopped
	 */
	fun cancel(): Boolean {
		paused = true
		return runBlocking { stopRecognizerThread() }
	}

	/**
	 * Shutdown the recognizer and release the recorder
	 */
	fun shutdown() {
		recorder.release()
	}

	fun setPause(paused: Boolean) {
		this.paused = paused
	}

	/**
	 * Resets recognizer in a thread, starts recognition over again
	 */
	fun reset() {
		reset = true
	}

	private suspend fun startRecognizer(
		listener: RecognitionListener,
		timeout: Int = NO_TIMEOUT
	) {
		var remainingSamples: Int

		val timeoutSamples: Int = if (timeout != NO_TIMEOUT) {
			timeout * sampleRate / 1000
		} else {
			NO_TIMEOUT
		}

		remainingSamples = timeoutSamples

		recorder.startRecording()
		if (recorder.recordingState == AudioRecord.RECORDSTATE_STOPPED) {
			recorder.stop()
			val ioe = IOException(
				"Failed to start recording. Microphone might be already in use."
			)
			withContext(Dispatchers.Main) { listener.onError(ioe) }
		}
		val buffer = ShortArray(bufferSize)
		while (!interrupt
			&& (timeoutSamples == NO_TIMEOUT || remainingSamples > 0)
		) {
			val nread = recorder.read(buffer, 0, buffer.size)
			if (paused) {
				continue
			}
			if (reset) {
				recognizer.reset()
				reset = false
			}
			if (nread < 0) throw RuntimeException("error reading audio buffer")
			if (recognizer.acceptWaveform(buffer)) {
				val result = recognizer.result
				withContext(Dispatchers.Main) { listener.onResult(result) }
			} else {
				val partialResult = recognizer.partialResult
				withContext(Dispatchers.Main) { listener.onPartialResult(partialResult) }
			}
			if (timeoutSamples != NO_TIMEOUT) {
				remainingSamples -= nread
			}
		}

		recorder.stop()

		if (!paused) {
			// If we met timeout signal that speech ended
			if (timeoutSamples != NO_TIMEOUT && remainingSamples <= 0) {
				withContext(Dispatchers.Main) { listener.onTimeout() }
			} else {
				val finalResult = recognizer.finalResult
				withContext(Dispatchers.Main) { listener.onFinalResult(finalResult) }
			}
		}
	}

	companion object {
		private const val NO_TIMEOUT = -1
		private const val BUFFER_SIZE_SECONDS = 0.2f
	}
}