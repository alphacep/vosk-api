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

package org.vosk

/**
 * 26 / 12 / 2022
 *
 * Control overarching features of libvosk.
 */
expect object Vosk {
	/**
	 * Set log level for Kaldi messages
	 *
	 *  @param logLevel the level
	 */
	fun setLogLevel(logLevel: LogLevel)

	/**
	 *  Init, automatically select a CUDA device and allow multithreading.
	 *  Must be called once from the main thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	fun gpuInit()


	/**
	 *  Init CUDA device in a multi-threaded environment.
	 *  Must be called for each thread.
	 *  Has no effect if HAVE_CUDA flag is not set.
	 */
	fun gpuThreadInit()
}