package org.vosk

@Throws(IOException::class)
inline fun ioException(path: String): IOException =
	IOException("Failed to find model: $path")