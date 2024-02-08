package org.vosk.test;

import java.io.FileInputStream;
import java.io.BufferedInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;

import org.junit.Test;
import org.junit.Assert;

import javax.sound.sampled.AudioSystem;
import javax.sound.sampled.UnsupportedAudioFileException;

import org.vosk.LogLevel;
import org.vosk.Recognizer;
import org.vosk.LibVosk;
import org.vosk.Model;

public class DecoderTest {

    @Test
    public void decoderTest() throws IOException, UnsupportedAudioFileException, InterruptedException {
        LibVosk.setLogLevel(LogLevel.DEBUG);

        try (Model model = new Model("../../python/example/vosk-model-small-ru");
            InputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(new FileInputStream("../../python/example/test.wav")));
            Recognizer recognizer = new Recognizer(model, 16000)) {

            int nbytes;
            byte[] b = new byte[1024];
            while ((nbytes = ais.read(b)) >= 0) {
                recognizer.acceptWaveForm(b, nbytes);
                while (recognizer.getPendingResults() > 0) {
                    Thread.sleep(50);
                }
                System.out.println(recognizer.getResult());
                recognizer.popResult();
            }
        }
        Assert.assertTrue(true);
    }
}
