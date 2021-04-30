package org.vosk;

import com.sun.jna.PointerType;

public class Recognizer extends PointerType implements AutoCloseable {
    private static final int DEFAULT_N_BEST_MATCHES_DEPTH = 1;

    public Recognizer(Model model, float sampleRate) {
        super(LibVosk.vosk_recognizer_new(model, sampleRate));
    }

    public Recognizer(Model model, SpeakerModel spkModel, float sampleRate) {
        super(LibVosk.vosk_recognizer_new_spk(model.getPointer(), spkModel.getPointer(), sampleRate));
    }

    public Recognizer(Model model, float sampleRate, String grammar) {
        super(LibVosk.vosk_recognizer_new_grm(model.getPointer(), sampleRate, grammar));
    }

    public boolean acceptWaveForm(byte[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform(this.getPointer(), data, len);
    }

    public boolean acceptWaveForm(short[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform_s(this.getPointer(), data, len);
    }

    public boolean acceptWaveForm(float[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform_f(this.getPointer(), data, len);
    }

    public String getResult() {
        return getResult(DEFAULT_N_BEST_MATCHES_DEPTH);
    }

    public String getResult(int nBestMatches) {
        return LibVosk.vosk_recognizer_result(this.getPointer(), nBestMatches);
    }

    public String getPartialResult() {
        return LibVosk.vosk_recognizer_partial_result(this.getPointer());
    }

    public String getFinalResult() {
        return getFinalResult(DEFAULT_N_BEST_MATCHES_DEPTH);
    }

    public String getFinalResult(int nBestMatches) {
        return LibVosk.vosk_recognizer_final_result(this.getPointer(), nBestMatches);
    }

    @Override
    public void close() {
        LibVosk.vosk_recognizer_free(this.getPointer());
    }
}
