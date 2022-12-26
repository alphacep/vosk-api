/*
 * Copyright 2020 Alpha Cephei Inc. & Doomsdayrs
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
 * 26 / 12 / 2022
 */
actual class SpeakerModel : PointerType, AutoCloseable {
	actual constructor(path: String) : super(LibVosk.vosk_spk_model_new(path))

	actual fun free() {
		LibVosk.vosk_spk_model_free(this)
	}

	override fun close() {
		free()
	}

}