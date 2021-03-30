package org.vosk;

import com.sun.jna.PointerType;

public class Recognizer extends PointerType implements AutoCloseable {
    public Recognizer(Model model, float sampleRate) {
        super(LibVosk.vosk_recognizer_new(model, sampleRate));
    }

    public Recognizer(Model model, SpeakerModel spkrModel, float sampleRate) {
        super(LibVosk.vosk_recognizer_new_spk(model.getPointer(), spkrModel.getPointer(), sampleRate));
    }

    public boolean acceptWaveForm(byte[] data, int len) {
        return LibVosk.vosk_recognizer_accept_waveform(this.getPointer(), data, len);
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

    @Override
    public void close() {
        LibVosk.vosk_recognizer_free(this.getPointer());
    }
}
