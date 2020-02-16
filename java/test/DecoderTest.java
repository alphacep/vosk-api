package test;

import java.io.File;
import java.io.FileInputStream;
import java.io.FileOutputStream;
import java.io.DataOutputStream;
import java.io.IOException;
import java.net.URL;
import java.nio.*;

import org.kaldi.KaldiRecognizer;
import org.kaldi.Model;
import org.kaldi.SpkModel;

public class DecoderTest {
    static {
        System.loadLibrary("vosk_jni");
    }

    public static void main(String args[]) throws IOException {
        FileInputStream ais = new FileInputStream(new File("../python/example/test.wav"));
        Model model = new Model("model-en");
        SpkModel spkModel = new SpkModel("model-spk");
        KaldiRecognizer rec = new KaldiRecognizer(model, spkModel, 16000.0f);

        int nbytes;
        byte[] b = new byte[4096];
        while ((nbytes = ais.read(b)) >= 0) {
            if (rec.AcceptWaveform(b, nbytes)) {
                System.out.println(rec.Result());
            } else {
                System.out.println(rec.PartialResult());
            }
        }
        System.out.println(rec.FinalResult());
    }
}
