package test;

import com.sun.jna.Native;
import com.sun.jna.Pointer;
import com.sun.jna.PointerType;

import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;


public class DecoderTest {


    public static void main(String[] args) throws IOException {
        final LibVosk libVosk = new LibVosk();
        libVosk.setLogLevel(LibVosk.LogLevel.DEBUG);

        try (LibVosk.Model model = new LibVosk.Model("model");
             InputStream ais = new FileInputStream("../python/example/test.wav");
             LibVosk.Recognizer recognizer = new LibVosk.Recognizer(model, 16000f)) {

            int nbytes;
            byte[] b = new byte[4096];
            while ((nbytes = ais.read(b)) >= 0) {
                if (recognizer.acceptWaveForm(b, nbytes)) {
                    System.out.println(recognizer.getResult());
                } else {
                    System.out.println(recognizer.getPartialResult());
                }
            }

            System.out.println(recognizer.getFinalResult());
        }
    }
}
