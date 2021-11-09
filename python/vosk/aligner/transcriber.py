import wave
import sys
import json

class Transcriber:
    '''Acoustic model
    There are align/realign parts:
        align part using basic LM/AM
        realign part using small personal LM/AM
    Output recognized words 
    '''
    def transcribe(recognizer, wavfile, chunk_end=None, duration=None):
        read_frames = 0
        if chunk_end == None and duration == None: # case of align
            duration = wavfile.getnframes() / float(wavfile.getframerate())
            frames = int(duration * wavfile.getframerate())
            if wavfile.getnchannels() != 1 or wavfile.getsampwidth() != 2 or wavfile.getcomptype() != "NONE":
                print("Audio file must be WAV format mono PCM.")
                exit (1)
        else: # case of realign
            duration = duration
            frames = chunk_end
        result = [] 
        recognizer.SetWords(True)
        while True:
            buf = wavfile.readframes(4000) # getting parts of wavfile
            read_frames = read_frames + len(buf)
            if len(buf) == 0:
                break
            if read_frames > frames and chunk_end is not None:
                    break
            if recognizer.AcceptWaveform(buf):
                res = json.loads(recognizer.Result())
                if 'result' in res:
                    result.extend(res['result'])
        res = json.loads(recognizer.FinalResult())
        if 'result' in res:
            result.extend(res['result'])
        words = result
        return words, duration
