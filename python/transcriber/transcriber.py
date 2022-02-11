import json
import sys
import subprocess
import time

from datetime import datetime as dt
from vosk import KaldiRecognizer

class Transcriber:

    def transcribe(model, wf):
        rec = KaldiRecognizer(model, 16000)
        tot_samples = 0
        final_result = ''
    
        while True:
            data = wf.stdout.read(4000)
            if len(data) == 0:
                break

            if rec.AcceptWaveform(data):
                tot_samples += len(data)
                result = json.loads(rec.Result())
                final_result += result['text'] + ' '

        return final_result, tot_samples

    def resample_ffmpeg(infile):
        process = subprocess.Popen(
            ['ffmpeg', '-loglevel', 'quiet', '-i', 
            infile, 
            '-ar', '16000','-ac', '1', '-f', 's16le', '-'], 
            stdout=subprocess.PIPE)
        return process

    def get_time():
        start_time = dt.now()
        return start_time

    def send_time(start_time):
        script_time = str(dt.now() - start_time)
        seconds = script_time[5:7].strip('0')
        mcseconds = script_time[8:].strip('0')
        return script_time.strip(':0'), seconds, mcseconds 
