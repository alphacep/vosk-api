#!/usr/bin/env python3


from vosk_python import Processor

proc = Processor("ru_itn_tagger.fst", "ru_itn_verbalizer.fst")
