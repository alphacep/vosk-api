package org.vosk.json

import kotlinx.serialization.SerialName
import kotlinx.serialization.Serializable

/**
 * 26 / 12 / 2022
 */
@Serializable
data class PartialResultOutput(
	val partial: String,
	@SerialName("partial_result")
	val partialResult: List<Result> = emptyList(),
)
