import json
import subprocess
import time
import requests
import urllib.request
import zipfile
import srt
import datetime
import os
import re
import logging

from vosk import KaldiRecognizer
from pathlib import Path


WORDS_PER_LINE = 7
MODEL_PRE_URL = 'https://alphacephei.com/vosk/models/'
MODEL_LIST_URL = MODEL_PRE_URL + 'model-list.json'

class Transcriber:

    def get_result_and_tot_samples(self, rec, process):
        tot_samples = 0
        result = []
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                tot_samples += len(data)
                result.append(json.loads(rec.Result())) 
        result.append(json.loads(rec.FinalResult()))
        return result, tot_samples

    def transcribe(self, model, process, args):
        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(True)
        result, tot_samples = self.get_result_and_tot_samples(rec, process)
        final_result = ''
        if args.outputtype == 'srt':
            subs = []
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
            final_result = srt.compose(subs)
        elif args.outputtype == 'txt':
            for part in result:
                final_result += part['text'] + ' '
        return final_result, tot_samples

    def resample_ffmpeg(self, infile):
        stream = subprocess.Popen(
            ['ffmpeg', '-nostdin', '-loglevel', 'quiet', '-i', 
            infile, 
            '-ar', '16000','-ac', '1', '-f', 's16le', '-'], 
            stdout=subprocess.PIPE)
        return stream

    def get_task_list(self, args):
        task_list = [(Path(args.input, fn), Path(args.output, Path(fn).stem).with_suffix('.' + args.outputtype)) for fn in os.listdir(args.input)]
        return task_list

    def list_models(self):
        response = requests.get(MODEL_LIST_URL)
        [print(model['name']) for model in response.json()]
        exit(1)

    def list_languages(self):
        response = requests.get(MODEL_LIST_URL)
        list_languages = set([language['lang'] for language in response.json()])
        print(*list_languages, sep='\n')
        exit(1)

    def check_args(self, args):
        if args.list_models == True:
            self.list_models()
        elif args.list_languages == True:
            self.list_languages()
