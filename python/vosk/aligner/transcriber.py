import wave
import sys
import json

class Transcriber:
    '''
    Acoustic model
    There are align/realign parts:
        align part using basic LM/AM
        realign part using small personam LM/AM
    Output recognized words
    '''
    def __init__(self, gen_hclg_filename):
        self.rec = gen_hclg_filename # LM

    def transcribe(self, wavfile, chunk=None, duration=None):
        if chunk == None: # case of align
            duration = wavfile.getnframes() / float(wavfile.getframerate()) 
            if wavfile.getnchannels() != 1 or wavfile.getsampwidth() != 2 or wavfile.getcomptype() != "NONE":
                print("Audio file must be WAV format mono PCM.")
                exit (1)
        else: # case of realign
            wavfile = chunk # get part of wavfile to realign
            duration = duration # get duration of the part
        result = [] 
        self.rec.SetWords(True)
        while True:
            buf = wavfile.readframes(4000) # getting parts of wavfile
            if len(buf) == 0:
                break
            if self.rec.AcceptWaveform(buf):
                res = json.loads(self.rec.Result())
                if 'result' in res:
                    result.extend(res['result'])
                words = result
        return words, duration
