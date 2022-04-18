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
MODEL_PRE_PATH = 'https://alphacephei.com/vosk/models/'
MODEL_LIST_URL = MODEL_PRE_PATH + 'model-list.json'

class Transcriber:

    def transcribe(self, model, process, args):
        rec = KaldiRecognizer(model, 16000)
        rec.SetWords(True)

        def get_result_and_tot_samples(rec, data, tot_samples, result):
            if rec.AcceptWaveform(data):
                tot_samples += len(data)
                result.append(json.loads(rec.Result()))
            return result, tot_samples
        tot_samples = 0
        result = []
        while True:
            stream = process.stdout.read(4000)
            if len(stream) == 0:
                break
            result, tot_samples = get_result_and_tot_samples(rec, stream, tot_samples, result)
        result.append(json.loads(rec.FinalResult()))
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

    def get_file_list(self, args):
        arg_list = []
        [arg_list.append((Path(args.input, files), Path(args.output, Path(files).stem).with_suffix('.' + args.outputtype))) for files in os.listdir(args.input)]
        return arg_list

    def check_args(self, args):
    
        def models_list():
            response = requests.get(MODEL_LIST_URL)
            [print(model['name']) for model in response.json()]
            exit(1)

        def languages_list():
            language_list = []
            response = requests.get(MODEL_LIST_URL)
            [language_list.append(language['lang']) for language in response.json() if language['lang'] not in language_list]
            print(*language_list, sep='\n')
            exit(1)

        if args.models_list == True:
            models_list()
        elif args.languages_list == True:
            languages_list()

    def get_model_name_using_model_name_arg(self, args, models_path):
        if not Path.is_dir(Path(models_path, args.model_name)):
            response = requests.get(MODEL_LIST_URL)
            result_model = [model['name'] for model in response.json() if model['name'] == args.model_name]
            if result_model == []:
                logging.info('model name "%s" does not exist, set -models_list to see available models' % (args.model_name))
                exit(1)
            else:
                result_model = result_model[0]
        else:
            result_model = args.model_name
        return result_model

    def get_model_name_using_lang_arg(self, args, models_path):
        model_file_list = os.listdir(models_path)
        model_file = [model for model in model_file_list if re.match(f"vosk-model(-small)?-{args.lang}", model)]
        if model_file == []:
            response = requests.get(MODEL_LIST_URL)
            result_model = [model['name'] for model in response.json() if model['lang'] == args.lang and model['type'] == 'small' and model['obsolete'] == 'false']
            if result_model == []:
                logging.info('language "%s" does not exist, set -languages_list to see available languages' % (args.lang))
                exit(1)
            else:
                result_model = result_model[0]
        else:
            result_model = model_file[0]
        return result_model
        
    def download_model(self, model_location, models_path):
        if not Path(model_location).exists():
            model_zip = model_location + '.zip'
            urllib.request.urlretrieve(MODEL_PRE_PATH + model_location[len(str(Path(model_location).parent))+1:] + '.zip', model_zip)
            with zipfile.ZipFile(model_zip, 'r') as model_ref:
                model_ref.extractall(models_path)
            Path.unlink(Path(model_zip))
        model = Model(model_location)
        return model

    def get_model(self, args):    
        models_path = Path.home() / '.cache' / 'vosk'
        if not Path.is_dir(models_path):
            Path.mkdir(models_path)
        if args.lang == None:
            result_model = self.get_model_name_using_model_name_arg(args, models_path)
        else:
            result_model = self.get_model_name_using_lang_arg(args, models_path)
        model_location = str(Path(models_path, result_model))
        model = self.download_model(model_location, models_path)
        return model
