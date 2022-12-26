package org.vosk


/**
 * 26 / 12 / 2022
 */
actual object Vosk {
	actual fun setLogLevel(logLevel: LogLevel) {
		LibVosk.vosk_set_log_level(logLevel.value)
	}

	actual fun gpuInit() {
		LibVosk.vosk_gpu_init()
	}

	actual fun gpuThreadInit() {
		LibVosk.vosk_gpu_thread_init()
	}
}