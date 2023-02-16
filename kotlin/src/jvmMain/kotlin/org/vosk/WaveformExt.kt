package org.vosk

import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import kotlinx.coroutines.flow.flowOn
import org.vosk.json.*
import java.io.InputStream

/**
 * Feed an [InputStream] into a [Recognizer].
 *
 * The flow will emit an [WaveformResult] for each result parsed.
 *
 * This will close the [InputStream] at the end of reading.
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
fun InputStream.feed(recognizer: Recognizer): Flow<WaveformResult> =
	flow {
		val b = ByteArray(4096)

		while (read(b) >= 0) {
			if (recognizer.acceptWaveform(b)) {
				emit(WaveformResult.Result(recognizer.resultAsJson()))
			} else {
				emit(WaveformResult.PartialResult(recognizer.partialResultAsJson()))
			}
		}

		emit(WaveformResult.FinalResult(recognizer.finalResultAsJson()))
		close()
	}.flowOn(Dispatchers.IO)