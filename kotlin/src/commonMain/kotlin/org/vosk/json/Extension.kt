/*
 * Copyright 2023 Alpha Cephei Inc.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *     http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package org.vosk.json

import kotlinx.serialization.decodeFromString
import kotlinx.serialization.json.Json
import kotlinx.serialization.json.encodeToJsonElement
import org.vosk.Recognizer
import org.vosk.Model
import org.vosk.exception.RecognizerException

/*
 * 26 / 12 / 2022
 */

/**
 * Vosk JSON encoder
 */
val voskJson = Json { encodeDefaults = true }

/**
 * Get the result as a JSON object
 */
fun Recognizer.resultAsJson(): ResultOutput =
	voskJson.decodeFromString(result)

/**
 * Get the final result as a JSON object
 */
fun Recognizer.finalResultAsJson(): ResultOutput =
	voskJson.decodeFromString(finalResult)

/**
 * Get the partial result as a JSON object
 */
fun Recognizer.partialResultAsJson(): PartialResultOutput =
	voskJson.decodeFromString(partialResult)


/**
 * Create a [Recognizer], but using a list for grammar instead.
 *
 * The grammar list is converted into a JSON array
 */
@Throws(RecognizerException::class)
fun Recognizer(model: Model, sampleRate: Float, grammar: List<String>) =
	Recognizer(model, sampleRate, voskJson.encodeToJsonElement(grammar).toString())