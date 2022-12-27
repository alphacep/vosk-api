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

/**
 * Batch recognizer object
 *
 * 26 / 12 / 2022
 */
expect class BatchRecognizer {

	/**
	 * Creates batch recognizer object
	 */
	constructor(model: BatchModel, sampleRate: Float)

	/**
	 * Releases batch recognizer object
	 */
	fun free()

	/**
	 * Accept batch voice data
	 */
	fun acceptWaveform(data: ByteArray)

	/**
	 * Set NLSML output
	 * @param nlsml - boolean value
	 */
	fun setNLSML(nlsml: Boolean)

	/**
	 *  Closes the stream
	 */
	fun finishStream()

	/**
	 * Return results
	 */
	val frontResult: String

	/**
	 * Release and free first retrieved result
	 */
	fun pop()

	/**
	 * Get amount of pending chunks for more intelligent waiting
	 */
	val pendingChunks: Int
}