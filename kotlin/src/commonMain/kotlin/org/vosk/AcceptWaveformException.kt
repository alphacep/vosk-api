package org.vosk

/**
 * Thrown when a [Recognizer] cannot accept a givent waveform
 */
class AcceptWaveformException(data: Any) : Exception("Could not accept waveform: $data")