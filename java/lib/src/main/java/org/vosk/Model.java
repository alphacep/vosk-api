package org.vosk;

import com.sun.jna.PointerType;

public class Model extends PointerType implements AutoCloseable {
    public Model() {
    }

    public Model(String path) {
        super(LibVosk.vosk_model_new(path));
    }

    @Override
    public void close() {
        LibVosk.vosk_model_free(this.getPointer());
    }
}
