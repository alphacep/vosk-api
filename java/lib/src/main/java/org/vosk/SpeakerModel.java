package org.vosk;

import com.sun.jna.PointerType;
import java.io.IOException;

public class SpeakerModel extends PointerType implements AutoCloseable {
    public SpeakerModel() {
    }

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
