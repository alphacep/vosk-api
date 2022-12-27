package org.vosk.json

import kotlinx.serialization.Serializable

/**
 * 26 / 12 / 2022
 */
@Serializable
data class ResultOutput(
	val alternatives: List<Alternative> = emptyList(),
	val result: List<Result> = emptyList(),
	val text: String? = null
)
