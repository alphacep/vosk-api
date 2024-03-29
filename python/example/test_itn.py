#!/usr/bin/env python3

import wave
import sys

from vosk import Processor

proc = Processor("ru_itn_tagger.fst", "ru_itn_verbalizer.fst")
print (proc.process("у нас десять яблок"))
print (proc.process("у нас десять яблок и десять миллилитров воды точка"))
print (proc.process("мы пришли в восемь часов пять минут"))
