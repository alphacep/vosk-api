package org.vosk

import libvosk.vosk_set_log_level
import libvosk.vosk_gpu_init
import libvosk.vosk_gpu_thread_init

/**
 * 26 / 12 / 2022
 */
actual object Vosk {
	/** Set log level for Kaldi messages
	 *
	 *  @param logLevel the level
	 */
	actual fun setLogLevel(logLevel: LogLevel) {
		vosk_set_log_level(logLevel.value)
	}

	/**
	 *  Init, automatically select a CUDA device and allow multithreading.
	 *  Must be called once from the main thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	actual fun gpuInit() {
		vosk_gpu_init()
	}

	/**
	 *  Init CUDA device in a multi-threaded environment.
	 *  Must be called for each thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	actual fun gpuThreadInit() {
		vosk_gpu_thread_init()
	}
}