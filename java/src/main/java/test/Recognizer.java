package test;

import com.sun.jna.PointerType;

public class Recognizer extends PointerType implements AutoCloseable {
    public Recognizer(Model model) {
        super(LibVosk.vosk_recognizer_new(model, 16000));
    }

    public Recognizer(Model model, SpeakerModel spkrModel) {
        super(LibVosk.vosk_recognizer_new_spk(model.getPointer(), spkrModel.getPointer(), 16000));
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
