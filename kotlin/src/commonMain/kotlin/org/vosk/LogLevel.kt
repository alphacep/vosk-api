package org.vosk

/**
 * Log level for Kaldi messages.
 *
 * 26 / 12 / 2022
 */
enum class LogLevel(val value: Int) {

	/**
	 * Don't print info messages
	 */
	WARNINGS(-1),

	/**
	 * Default value to print info and error messages but no debug
	 */
	INFO(0),

	/**
	 * More verbose mode
	 */
	DEBUG(1);
}