package test;

import java.io.FileInputStream;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;

import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.UnsupportedAudioFileException;


public class DecoderTest {


    public static void main(String[] args) throws IOException, UnsupportedAudioFileException {
        final LibVosk libVosk = new LibVosk();
        libVosk.setLogLevel(LibVosk.LogLevel.DEBUG);

        try (LibVosk.Model model = new LibVosk.Model("model");
             InputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(new FileInputStream("../python/example/test.wav")));
             LibVosk.Recognizer recognizer = new LibVosk.Recognizer(model)) {

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
