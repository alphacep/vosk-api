package test;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.PointerType;

public class LibVosk {
    static {
        Native.register("vosk");
    }

    private static native void vosk_set_log_level(int level);

    private static native Pointer vosk_model_new(String path);

    private static native void vosk_model_free(Pointer model);

    private static native Pointer vosk_spk_model_new(String path);

    private static native void vosk_spk_model_free(Pointer model);

    private static native Pointer vosk_recognizer_new(Model model, float sample_rate);

    private static native Pointer vosk_recognizer_new_spk(Pointer model, Pointer spkModel, float sample_rate);

    private static native boolean vosk_recognizer_accept_waveform(Pointer recognizer, byte[] data, int len);

    private static native String vosk_recognizer_result(Pointer recognizer);

    private static native String vosk_recognizer_final_result(Pointer recognizer);

    private static native String vosk_recognizer_partial_result(Pointer recognizer);

    private static native void vosk_recognizer_free(Pointer recognizer);

    public enum LogLevel {
        WARNINGS(-1),  // Print warning and errors
        INFO(0),       // Print info, along with warning and error messages, but no debug
        DEBUG(1);      // Print debug info

        private final int value;

        private LogLevel(int value) {
            this.value = value;
        }

        public int getValue() {
            return this.value;
        }
    }

    public void setLogLevel(LogLevel loglevel) {
        vosk_set_log_level(loglevel.getValue());
    }

    public static class Model extends PointerType implements AutoCloseable {
        public Model() {
            super();
        }

        public Model(String path) {
            super(vosk_model_new(path));
        }

        @Override
        public void close() {
            vosk_model_free(this.getPointer());
        }
    }

    public static class SpeakerModel extends PointerType implements AutoCloseable {
        public SpeakerModel() {
            super();
        }

        public SpeakerModel(String path) {
            super(vosk_spk_model_new(path));
        }

        @Override
        public void close() {
            vosk_spk_model_free(this.getPointer());
        }
    }

    public static class Recognizer extends PointerType implements AutoCloseable {
        public Recognizer(Model model, float sampleRate) {
            super(vosk_recognizer_new(model, sampleRate));
        }

        public Recognizer(Model model, SpeakerModel spkrModel, float sampleRate) {
            super(vosk_recognizer_new_spk(model.getPointer(), spkrModel.getPointer(), sampleRate));
        }

        public boolean acceptWaveForm(byte[] data, int len) {
            return vosk_recognizer_accept_waveform(this.getPointer(), data, len);
        }

        public String getResult() {
            return vosk_recognizer_result(this.getPointer());
        }

        public String getPartialResult() {
            return vosk_recognizer_partial_result(this.getPointer());
        }

        public String getFinalResult() {
            return vosk_recognizer_final_result(this.getPointer());
        }

        @Override
        public void close() {
            vosk_recognizer_free(this.getPointer());
        }
    }
}
