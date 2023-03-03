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

import kotlinx.serialization.Serializable

/**
 * Represents a result for any given word.
 *
 * @since 26 / 12 / 2022
 */
@Serializable
data class Result(
	val conf: Double? = null,
	val end: Double,
	val start: Double,
	val word: String,
)
