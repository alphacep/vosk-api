package org.vosk.json

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import org.vosk.Recognizer

/*
 * 26 / 12 / 2022
 */

val voskJson = Json { encodeDefaults = true }

fun Recognizer.resultAsJson(): ResultOutput =
	voskJson.decodeFromString(result)

fun Recognizer.finalResultAsJson(): ResultOutput =
	voskJson.decodeFromString(finalResult)

fun Recognizer.partialResultAsJson(): PartialResultOutput =
	voskJson.decodeFromString(partialResult)