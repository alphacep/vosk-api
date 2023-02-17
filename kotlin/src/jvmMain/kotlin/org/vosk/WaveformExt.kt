package org.vosk

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import kotlinx.coroutines.flow.map
import org.vosk.json.*

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
