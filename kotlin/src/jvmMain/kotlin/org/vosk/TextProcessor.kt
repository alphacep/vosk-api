/*
 * Copyright 2024 Alpha Cephei Inc.
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

package org.vosk

import com.sun.jna.PointerType

/**
 * Inverse text normalization
 *
 * @since 2024/06/19
 */
actual class TextProcessor :
	Freeable, PointerType, AutoCloseable {

	/**
	 * Create text processor
	 */
	actual constructor(tagger: Char, verbalizer: Char) :
			super(LibVosk.vosk_text_processor_new(tagger, verbalizer))


	/** Release text processor */
	actual override fun free() {
		LibVosk.vosk_text_processor_free(this)
	}

	/** Convert string */
	actual fun itn(input: Char): Char =
		LibVosk.vosk_text_processor_itn(this, input)

	/**
	 * @see free
	 */
	override fun close() {
		free()
	}
}