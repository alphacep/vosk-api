package test;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.*;

import jnr.ffi.LibraryLoader;
import jnr.ffi.Pointer;

public class DecoderTest {
    public static interface LibVosk {
        void vosk_set_log_level(int level);
        Pointer vosk_model_new(String path);
        void vosk_model_free(Pointer model);
        Pointer vosk_recognizer_new(Pointer model, float sample_rate);
        boolean vosk_recognizer_accept_waveform(Pointer recognizer, Buffer data, int len);
        String vosk_recognizer_result(Pointer recognizer);
        String vosk_recognizer_final_result(Pointer recognizer);
        String vosk_recognizer_partial_result(Pointer recognizer);
        void vosk_recognizer_free(Pointer recognizer);
    }

    public static void main(String[] args) throws IOException {
        LibVosk libvosk = LibraryLoader.create(LibVosk.class).search(".").load("vosk");

        libvosk.vosk_set_log_level(0);
        Pointer model = libvosk.vosk_model_new("model");

        FileInputStream ais = new FileInputStream(new File("../python/example/test.wav"));
        Pointer rec = libvosk.vosk_recognizer_new(model, 16000.0f);

        int nbytes;
        byte[] b = new byte[4096];
        while ((nbytes = ais.read(b)) >= 0) {
            Buffer buf = ByteBuffer.wrap(b);
            if (libvosk.vosk_recognizer_accept_waveform(rec, buf, nbytes)) {
                System.out.println(libvosk.vosk_recognizer_result(rec));
            } else {
                System.out.println(libvosk.vosk_recognizer_partial_result(rec));
            }
         }
        System.out.println(libvosk.vosk_recognizer_final_result(rec));
        libvosk.vosk_recognizer_free(rec);
        libvosk.vosk_model_free(model);

    }
}
