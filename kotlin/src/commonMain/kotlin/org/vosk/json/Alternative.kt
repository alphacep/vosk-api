package org.vosk.json

import kotlinx.serialization.Serializable

/**
 * 26 / 12 / 2022
 */
@Serializable
data class Alternative(
	val confidence: Double,
	val result: List<Result> = emptyList(),
	val text: String
)
