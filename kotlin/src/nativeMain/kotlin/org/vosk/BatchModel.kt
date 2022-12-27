package org.vosk

import kotlinx.cinterop.CPointer
import libvosk.*

/**
 * Batch model object
 *
 * 26 / 12 / 2022
 */
actual class BatchModel(val pointer: CPointer<VoskBatchModel>) {
	/**
	 * Creates the batch recognizer object
	 */
	actual constructor(path: String) : this(vosk_batch_model_new(path)!!)

	/**
	 *  Releases batch model object
	 */
	actual fun free() {
		vosk_batch_model_free(pointer)
	}

	/**
	 * Wait for the processing
	 */
	actual fun await() {
		vosk_batch_model_wait(pointer)
	}
}