package org.vosk;

import com.sun.jna.PointerType;
import java.io.IOException;

/**
 * Helps to initialize speaker recognition for grammar-based recognizer.
 */
public class SpeakerModel extends PointerType implements AutoCloseable {
    public SpeakerModel() {
    }

    /**
     * Loads speaker model data from the file.
     *
     * The path must contain:
     * - a config file: mfcc.conf
     * - kaldi nnet: final.ext.raw
     * - mean.vec
     * - transform.mat
     *
     * @param path the path of the model on the filesystem
     * @throws IOException if the model could not be created
     *
     * @see <a href="http://kaldi-asr.org/doc/structkaldi_1_1MfccOptions.html">Kaldi MfccOptions</a>
     * @see <a href="http://kaldi-asr.org/doc/classkaldi_1_1nnet3_1_1Nnet.html">Kaldi Nnet</a>
     */
    public SpeakerModel(String path) throws IOException {
        super(LibVosk.vosk_spk_model_new(path));

        if (getPointer() == null) {
            throw new IOException("Failed to create a speaker model");
        }
    }

    @Override
    public void close() {
        LibVosk.vosk_spk_model_free(this.getPointer());
    }
}
