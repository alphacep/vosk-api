/**
 * 26 / 12 / 2022
 */

import org.vosk.*
import java.io.BufferedInputStream
import java.io.FileInputStream
import javax.sound.sampled.AudioSystem

class DecoderDemo {
	companion object {
		@JvmStatic
		fun main(array: Array<String>) {
			System.load("/usr/local/lib64/libvosk/libvosk.so")
			Vosk.setLogLevel(LogLevel.DEBUG)
			Model("/home/doomsdayrs/Downloads/vosk-model-small-en-us-0.15/").use { model ->
				AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream("../../python/example/test.wav")))
					.use { ais ->
						Recognizer(model, 16000f).apply {
							setWords(true)
							setPartialWords(true)
							setMaxAlternatives(3)
						}.use { recognizer ->
							val b = ByteArray(4096)
							while (ais.read(b) >= 0) {
								if (recognizer.acceptWaveform(b)) {
									println(recognizer.result())
								} else {
									println(recognizer.partialResult())
								}
							}
							println(recognizer.finalResult())
						}
					}
			}
		}
	}
}
