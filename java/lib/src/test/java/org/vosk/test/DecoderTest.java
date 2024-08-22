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
import org.vosk.TextProcessor;

public class DecoderTest {

    @Test
    public void decoderTest() throws IOException, UnsupportedAudioFileException {
        LibVosk.setLogLevel(LogLevel.DEBUG);

        try (Model model = new Model("model");
            InputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(new FileInputStream("../../python/example/test.wav")));
            Recognizer recognizer = new Recognizer(model, 16000)) {

            recognizer.setMaxAlternatives(10);
            recognizer.setWords(true);
            recognizer.setPartialWords(true);

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
        Assert.assertTrue(true);
    }

    @Test
    public void decoderTestShort() throws IOException, UnsupportedAudioFileException {
        LibVosk.setLogLevel(LogLevel.DEBUG);

        try (Model model = new Model("model");
            InputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(new FileInputStream("../../python/example/test.wav")));
            Recognizer recognizer = new Recognizer(model, 16000)) {

            int nbytes;
            byte[] b = new byte[4096];
            short[] s = new short[2048];
            while ((nbytes = ais.read(b)) >= 0) {
                ByteBuffer.wrap(b).order(ByteOrder.LITTLE_ENDIAN).asShortBuffer().get(s);
                if (recognizer.acceptWaveForm(s, nbytes / 2)) {
                    System.out.println(recognizer.getResult());
                } else {
                    System.out.println(recognizer.getPartialResult());
                }
            }

            System.out.println(recognizer.getFinalResult());
        }
        Assert.assertTrue(true);
    }

    @Test
    public void decoderTestGrammar() throws IOException, UnsupportedAudioFileException {
        LibVosk.setLogLevel(LogLevel.DEBUG);

        try (Model model = new Model("model");
            InputStream ais = AudioSystem.getAudioInputStream(new BufferedInputStream(new FileInputStream("../../python/example/test.wav")));
            Recognizer recognizer = new Recognizer(model, 16000, "[\"one two three four five six seven eight nine zero oh\"]")) {

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
        Assert.assertTrue(true);
    }


    @Test(expected = IOException.class)
    public void decoderTestException() throws IOException {
        Model model = new Model("model_missing");
    }

    @Test
    public void testItn() throws IOException {
        TextProcessor p = new TextProcessor("model/itn/en_itn_tagger.fst", "model/itn/en_itn_verbalizer.fst");
        System.out.println(p.itn("as easy as one two three"));
    }
}
