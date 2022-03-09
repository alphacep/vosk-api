import json
import sys
import subprocess
import time
import os
import requests
import urllib.request
import zipfile
import srt
import datetime

from datetime import datetime as dt
from vosk import KaldiRecognizer


class Transcriber:
    
    def transcribe(model, process, outputdata, outputtype):
        rec = KaldiRecognizer(model, 16000)
        WORDS_PER_LINE = 7
        tot_samples = 0
        final_result = ''
        result = list()
        subs = list()
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if outputtype == 'txt':
                if rec.AcceptWaveform(data):
                    tot_samples += len(data)
                    result.append(json.loads(rec.Result()))
            elif outputtype == 'srt':
                rec.SetWords(True)
                if rec.AcceptWaveform(data):
                    tot_samples += len(data)
                    result.append(json.loads(rec.Result()))
        result.append(json.loads(rec.FinalResult()))
        if outputtype == 'srt':
            for i, res in enumerate(result):
                if not 'result' in res:
                    continue
                words = res['result']
                for j in range(0, len(words), WORDS_PER_LINE):
                    line = words[j : j + WORDS_PER_LINE]
                    s = srt.Subtitle(index=len(subs),
                            content = ' '.join([l['word'] for l in line]),
                            start=datetime.timedelta(seconds=line[0]['start']),
                            end=datetime.timedelta(seconds=line[-1]['end']))
                    subs.append(s)
        if outputtype == 'srt':
            final_result = srt.compose(subs)
        elif outputtype == 'txt':
            for i in range(len(result)):
                final_result += result[i]['text'] + ' '
        return final_result, tot_samples
    
    def resample_ffmpeg(infile):
        process = subprocess.Popen(
            ['ffmpeg', '-nostdin', '-loglevel', 'quiet', '-i', 
            infile, 
            '-ar', '16000','-ac', '1', '-f', 's16le', '-'], 
            stdout=subprocess.PIPE)
        return process
    
    def get_time():
        start_time = dt.now()
        return start_time
    
    def send_time(start_time):
        script_time = str(dt.now() - start_time)
        seconds = script_time[5:8].strip('0')
        mcseconds = script_time[8:].strip('0')
        return script_time.strip(':0'), seconds.rstrip('.'), mcseconds
    
    def process_dir(model, inputdata, outputdata, outputtype, log):
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
