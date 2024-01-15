package org.vosk;

import com.sun.jna.PointerType;
import java.io.IOException;

public class Recognizer extends PointerType implements AutoCloseable {
    /**
     * Creates the recognizer object.
     *
     * The recognizers process the speech and return text using shared model data
     * @param model       VoskModel containing static data for recognizer. Model can be
     *                    shared across recognizers, even running in different threads.
     * @param sampleRate The sample rate of the audio you are going to feed into the recognizer.
     *                    Make sure this rate matches the audio content, it is a common
     *                    issue causing accuracy problems.
     * @throws IOException if the recognizer could not be created
     */
    public Recognizer(Model model, float sampleRate) throws IOException {
        super(LibVosk.vosk_recognizer_new(model, sampleRate));

        if (getPointer() == null) {
            throw new IOException("Failed to create a recognizer");
        }
    }

    /**
     * Accept and process new chunk of voice data.
     *
     *  @param data - audio data in PCM 16-bit mono format
     *  @param len - length of the audio data
     *  @return 1 if silence is occurred and you can retrieve a new utterance with result method
     *           0 if decoding continues
     *           -1 if exception occurred
     */
    public boolean acceptWaveForm(byte[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform(this.getPointer(), data, len);
    }

    public boolean acceptWaveForm(short[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform_s(this.getPointer(), data, len);
    }

    public boolean acceptWaveForm(float[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform_f(this.getPointer(), data, len);
    }

    /**
     * Returns speech recognition result
     *
     * @return the result in JSON format which contains decoded line, decoded
     *          words, times in seconds and confidences. You can parse this result
     *          with any json parser
     *
     * <pre>
     *  {
     *    "text" : "what zero zero zero one"
     *  }
     * </pre>
     *
     * If alternatives enabled it returns result with alternatives, see also #setMaxAlternatives().
     *
     * If word times enabled returns word time, see also #setWordTimes().
     */
    public String getResult() {
        return LibVosk.vosk_recognizer_result(this.getPointer());
    }

    /**
     * Returns partial speech recognition.
     *
     * @return partial speech recognition text which is not yet finalized.
     *          result may change as recognizer process more data.
     *
     * <pre>
     * {
     *    "partial" : "cyril one eight zero"
     * }
     * </pre>
     */
    public String getPartialResult() {
        return LibVosk.vosk_recognizer_partial_result(this.getPointer());
    }

    /**
     * Returns speech recognition result. Same as result, but doesn't wait for silence.
     *  You usually call it in the end of the stream to get final bits of audio. It
     *  flushes the feature pipeline, so all remaining audio chunks got processed.
     *
     *  @return speech result in JSON format.
     */
    public String getFinalResult() {
        return LibVosk.vosk_recognizer_final_result(this.getPointer());
    }

    /**
     * Resets the recognizer.
     * Resets current results so the recognition can continue from scratch.
     */
    public void reset() {
        LibVosk.vosk_recognizer_reset(this.getPointer());
    }

    /**
     * Releases recognizer object.
     * Underlying model is also unreferenced and if needed, released.
     */
    @Override
    public void close() {
        LibVosk.vosk_recognizer_free(this.getPointer());
    }
}
