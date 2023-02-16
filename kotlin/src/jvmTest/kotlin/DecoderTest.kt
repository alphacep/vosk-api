import kotlinx.coroutines.ExperimentalCoroutinesApi
import kotlinx.coroutines.test.runTest
import org.vosk.*
import java.io.BufferedInputStream
import java.io.FileInputStream
import java.io.IOException
import java.nio.ByteBuffer
import java.nio.ByteOrder
import javax.sound.sampled.AudioSystem
import javax.sound.sampled.UnsupportedAudioFileException
import kotlin.test.Test

class DecoderTest {
	val modelPath = System.getenv("MODEL")
	val testFile = System.getenv("AUDIO")

	init {
		System.load(System.getenv("LIBRARY"))
		Vosk.setLogLevel(LogLevel.DEBUG)
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTest() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(model, 16000f).apply {
						setMaxAlternatives(10)
						setWords(true)
						setPartialWords(true)
					}.use { recognizer ->
						val b = ByteArray(4096)
						while (ais.read(b) >= 0) {
							if (recognizer.acceptWaveform(b)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@OptIn(ExperimentalCoroutinesApi::class)
	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestFlow() {
		runTest {
			Model(modelPath).use { model ->
				Recognizer(model, 16000f).apply {
					setMaxAlternatives(10)
					setWords(true)
					setPartialWords(true)
				}.use { recognizer ->
					AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
						.feed(recognizer).collect {
							println(it)
						}
				}
			}
		}
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestShort() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(model, 16000f).use { recognizer ->
						val b = ByteArray(4096)
						val s = ShortArray(2048)
						while (ais.read(b) >= 0) {
							ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(s)
							if (recognizer.acceptWaveform(s)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@Test
	@Throws(IOException::class, UnsupportedAudioFileException::class)
	fun decoderTestGrammar() {
		Model(modelPath).use { model ->
			AudioSystem.getAudioInputStream(BufferedInputStream(FileInputStream(testFile)))
				.use { ais ->
					Recognizer(
						model, 16000f, "[\"one two three four five six seven eight nine zero oh\"]"
					).use { recognizer ->
						val b = ByteArray(4096)
						while (ais.read(b) >= 0) {
							if (recognizer.acceptWaveform(b)) {
								println(recognizer.result)
							} else {
								println(recognizer.partialResult)
							}
						}
						println(recognizer.finalResult)
					}
				}
		}
	}

	@Test
	fun decoderTestException() {
		try {
			val model = Model("model_missing")
			assert(false)
		} catch (e: IOException) {
			assert(true)
		}
	}
}