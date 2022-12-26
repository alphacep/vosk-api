package org.vosk

/**
 * 26 / 12 / 2022
 */
expect object Vosk {
	/** Set log level for Kaldi messages
	 *
	 *  @param logLevel the level
	 */
	fun setLogLevel(logLevel: LogLevel)

	/**
	 *  Init, automatically select a CUDA device and allow multithreading.
	 *  Must be called once from the main thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	fun gpuInit()


	/**
	 *  Init CUDA device in a multi-threaded environment.
	 *  Must be called for each thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	fun gpuThreadInit()
}