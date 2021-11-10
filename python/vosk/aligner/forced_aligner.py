from . import diff_align
from . import recognizer
from . import metasentence
from . import multipass
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
        self.ks = transcript
        self.ms = metasentence.MetaSentence(self.ks, self.model)
        self.recognizer = recognizer.recognize(self.ks, self.model)

    def transcribe(self, wavfile, progress_cb=None, logging=None):
        words = transcriber.transcribe(self.recognizer, wavfile)

        def unalign(words):
            NFIA = len([X for X in words if (X.not_found_in_audio())])
            NFIT = len([X for X in words if (X.not_found_in_transcript())])
            amount = NFIA + NFIT
            length = len(words)
            return amount, length

        # Align words
        words = diff_align.align(words, self.ms)

        # Perform a second-pass with unaligned words
        if logging is not None:
            amount, length = unalign(words)
            logging.info("%d unaligned words (of %d)", amount, length)

        if amount != 0:
            progress_cb({'status': 'ALIGNING'})
            words = multipass.realign(words, self.ms, self.model)

        if amount != 0:
            amount, length = unalign(words)
            logging.info("after 2nd pass: %d unaligned words (of %d)", amount, length)
        
        return Transcription(words=words, transcript=self.ks)

