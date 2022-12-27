package org.vosk

/*
 * 26 / 12 / 2022
 */

/**
 * Converts a boolean to an int
 */
internal inline fun Boolean.toInt() = if (this) 1 else 0

/**
 * Converts an int to a boolean
 */
internal inline fun Int.toBoolean() = this == 1