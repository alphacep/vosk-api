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

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import org.vosk.json.WaveformResult
import org.vosk.json.finalResultAsJson
import org.vosk.json.partialResultAsJson
import org.vosk.json.resultAsJson

/**
 * Feed an [Flow] of [ByteArray] into a [Recognizer].
 *
 * The returned flow will emit an [WaveformResult] for each result parsed.
 *
 * This expects a null terminator to signify the end of a stream.
 *
 * This will not close the [recognizer] at the end of reading.
 *
 * Any exceptions will be fed into the flow,
 *  and should be collected via [kotlinx.coroutines.flow.catch].
 *
 * Flows on [Dispatchers.IO] to prevent blocking the main thread.
 *
 * @see [Recognizer.acceptWaveform]
 */
fun Flow<ByteArray?>.feed(recognizer: Recognizer): Flow<WaveformResult> =
	map {
		if (it != null) {
			if (recognizer.acceptWaveform(it)) {
				WaveformResult.Result(recognizer.resultAsJson())
			} else {
				WaveformResult.PartialResult(recognizer.partialResultAsJson())
			}
		} else {
			WaveformResult.FinalResult(recognizer.finalResultAsJson())
		}
	}.flowOn(Dispatchers.IO)
