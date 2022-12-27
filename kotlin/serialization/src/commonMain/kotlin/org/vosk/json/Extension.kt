package org.vosk.json

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import org.vosk.Recognizer

/*
 * 26 / 12 / 2022
 */

val json = Json { encodeDefaults = true }

fun Recognizer.resultAsJson(): ResultOutput =
	json.decodeFromString(result())

fun Recognizer.finalResultAsJson(): ResultOutput =
	json.decodeFromString(finalResult())

fun Recognizer.partialResultAsJson(): PartialResultOutput =
	json.decodeFromString(partialResult())