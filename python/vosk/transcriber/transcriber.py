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

from vosk import KaldiRecognizer, Model
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

    def get_model_by_name(self, args, models_path):
        if not Path.is_dir(Path(models_path, args.model_name)):
            response = requests.get(MODEL_LIST_URL)
            result = [model['name'] for model in response.json() if model['name'] == args.model_name]
            if result == []:
                logging.info('model name "%s" does not exist, request -list_models to see available models' % (args.model_name))
                exit(1)
            else:
                result = result[0]
        else:
            result = args.model_name
        return result

    def get_model_by_lang(self, args, models_path):
        model_file_list = os.listdir(models_path)
        model_file = [model for model in model_file_list if re.match(f"vosk-model(-small)?-{args.lang}", model)]
        if model_file == []:
            response = requests.get(MODEL_LIST_URL)
            result = [model['name'] for model in response.json() if model['lang'] == args.lang and model['type'] == 'small' and model['obsolete'] == 'false']
            if result == []:
                logging.info('language "%s" does not exist, request -list_languages to see available languages' % (args.lang))
                exit(1)
            else:
                result = result[0]
        else:
            result = model_file[0]
        return result

    def get_model(self, args):
        models_path = Path.home() / '.cache' / 'vosk'
        if not Path.is_dir(models_path):
            Path.mkdir(models_path)
        if args.lang == None:
            model_name = self.get_model_by_name(args, models_path)
        else:
            model_name = self.get_model_by_lang(args, models_path)
        model_location = models_path / model_name
        if not model_location.exists():
            model_zip = str(model_location) + '.zip'
            urllib.request.urlretrieve(MODEL_PRE_URL + model_name + '.zip', model_zip)
            with zipfile.ZipFile(model_zip, 'r') as model_ref:
                model_ref.extractall(models_path)
            Path.unlink(Path(model_zip))
        model = Model(str(model_location))
        return model
