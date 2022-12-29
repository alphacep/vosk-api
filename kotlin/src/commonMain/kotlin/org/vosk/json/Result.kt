package org.vosk.json

import kotlinx.serialization.Serializable

/**
 * 26 / 12 / 2022
 */
@Serializable
data class Result(
	val conf: Double? = null,
	val end: Double,
	val start: Double,
	val word: String,
)
