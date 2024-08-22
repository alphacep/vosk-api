package org.vosk;

import com.sun.jna.PointerType;

public class TextProcessor extends PointerType implements AutoCloseable {
    public TextProcessor() {
    }

    public TextProcessor(String verbalizer, String tagger) {
        super(LibVosk.vosk_text_processor_new(verbalizer, tagger));
    }

    @Override
    public void close() {
        LibVosk.vosk_text_processor_free(this.getPointer());
    }

    public String itn(String input) {
        return LibVosk.vosk_text_processor_itn(this.getPointer(), input);
    }
}
