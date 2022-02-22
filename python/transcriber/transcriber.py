import json
import sys
import subprocess
import time
import os

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

    def process_dirs(model, inputdata, outputdata, outputtype, log):
        files = os.listdir(inputdata)
        arg_list = list()
        input_dir = inputdata + '/'
        output_dir = outputdata + '/'
        extension_i = f".{files[0].split('.')[1]}"
        format_o = f".{outputtype}"
        input_list = [input_dir + each for each in files]
        output_list = [output_dir + each.replace(extension_i, format_o) for each in files]
        for i in range(len(input_list)):
            arg_list.extend([(model, input_list[i], output_list[i], outputtype, log)])
        return arg_list
