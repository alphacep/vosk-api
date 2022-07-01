package org.vosk;

import com.sun.jna.PointerType;

public class Recognizer extends PointerType implements AutoCloseable {
    public Recognizer(Model model, float sampleRate) {
        super(LibVosk.vosk_recognizer_new(model, sampleRate));
    }

    public Recognizer(Model model, float sampleRate, SpeakerModel spkModel) {
        super(LibVosk.vosk_recognizer_new_spk(model.getPointer(), sampleRate, spkModel.getPointer()));
    }

    public Recognizer(Model model, float sampleRate, String grammar) {
        super(LibVosk.vosk_recognizer_new_grm(model.getPointer(), sampleRate, grammar));
    }

    public void setMaxAlternatives(int maxAlternatives) {
        LibVosk.vosk_recognizer_set_max_alternatives(this.getPointer(), maxAlternatives);
    }

    public void setWords(boolean words) {
        LibVosk.vosk_recognizer_set_words(this.getPointer(), words);
    }

    public void setPartialWords(boolean partial_words) {
        LibVosk.vosk_recognizer_set_partial_words(this.getPointer(), partial_words);
    }

    public void setSpeakerModel(SpeakerModel spkModel) {
        LibVosk.vosk_recognizer_set_spk_model(this.getPointer(), spkModel.getPointer());
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
        return LibVosk.vosk_recognizer_result(this.getPointer());
    }

    public String getPartialResult() {
        return LibVosk.vosk_recognizer_partial_result(this.getPointer());
    }

    public String getFinalResult() {
        return LibVosk.vosk_recognizer_final_result(this.getPointer());
    }

    public void reset() {
        LibVosk.vosk_recognizer_reset(this.getPointer());
    }

    @Override
    public void close() {
        LibVosk.vosk_recognizer_free(this.getPointer());
    }
}
