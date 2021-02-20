package test;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.*;

import com.sun.jna.Library;
import com.sun.jna.Native;
import com.sun.jna.Platform;
import com.sun.jna.Pointer;

public class DecoderTest {
    public interface LibVosk extends Library {
        static LibVosk INSTANCE = (LibVosk) Native.loadLibrary("vosk", LibVosk.class);

        void vosk_set_log_level(int level);
        Pointer vosk_model_new(String path);
        void vosk_model_free(Pointer model);
        Pointer vosk_recognizer_new(Pointer model, float sample_rate);
        boolean vosk_recognizer_accept_waveform(Pointer recognizer, byte[] data, int len);
        String vosk_recognizer_result(Pointer recognizer);
        String vosk_recognizer_final_result(Pointer recognizer);
        String vosk_recognizer_partial_result(Pointer recognizer);
        void vosk_recognizer_free(Pointer recognizer);
    }

    public static void main(String[] args) throws IOException {
        LibVosk.INSTANCE.vosk_set_log_level(0);
        Pointer model = LibVosk.INSTANCE.vosk_model_new("model");

        FileInputStream ais = new FileInputStream(new File("../python/example/test.wav"));
        Pointer rec = LibVosk.INSTANCE.vosk_recognizer_new(model, 16000.0f);

        int nbytes;
        byte[] b = new byte[4096];
        while ((nbytes = ais.read(b)) >= 0) {
            if (LibVosk.INSTANCE.vosk_recognizer_accept_waveform(rec, b, nbytes)) {
                System.out.println(LibVosk.INSTANCE.vosk_recognizer_result(rec));
            } else {
                System.out.println(LibVosk.INSTANCE.vosk_recognizer_partial_result(rec));
            }
         }
        System.out.println(LibVosk.INSTANCE.vosk_recognizer_final_result(rec));
        LibVosk.INSTANCE.vosk_recognizer_free(rec);
        LibVosk.INSTANCE.vosk_model_free(model);
    }
}
