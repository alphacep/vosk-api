from .diff_align import align
from .text_processor import text_processor
from .metasentence import MetaSentence as metasentence
from .multipass import realign
from .transcriber import Transcriber as transcriber
from .transcription import Transcription

class ForcedAligner():
    '''Head class of the program which control all basic things, providing
    language and acoustic models input args and getting results. ForcedAligner
    is watching for aligning process(align/realign parts) allow to see
    alignment results. Output word sequence contain whole information each
    word(status, timings, etc).
    '''
    def __init__(self, transcript, model):
        self.model = model
        self.transcript = transcript
        self.ms = metasentence(self.transcript, self.model)
        self.text = text_processor(self.transcript, self.model)
    
    def get_number_unsuccessful_words(self, align_words):
        NFIA = len([X for X in align_words if (X.not_found_in_audio())])
        NFIT = len([X for X in align_words if (X.not_found_in_transcript())])
        return NFIA + NFIT

    def transcribe(self, wavfile, progress_cb=None, logging=None):
        words = transcriber.transcribe(self.text, wavfile)
        align_words = align(words, self.ms) # align
        unsuccessful_number = self.get_number_unsuccessful_words(align_words)
        logging.info("%d unaligned words (of %d)", unsuccessful_number, len(align_words))
        if unsuccessful_number != 0:
            realign_words = realign(align_words, self.ms, self.model, wavfile) # realign
            unsuccessful_number = self.get_number_unsuccessful_words(realign_words)
            logging.info("after 2nd pass: %d unaligned words (of %d)", unsuccessful_number, len(realign_words))
        return Transcription(words=realign_words, transcript=self.transcript)

