#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import json
import shlex

from pathlib import Path
from vosk import Model, KaldiRecognizer, SetLogLevel
from multiprocessing.dummy import Pool
from queue import Queue

SetLogLevel(0)

SAMPLE_RATE = 16000
MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
MODEL_LIST_URL = MODEL_PRE_URL + "model-list.json"
MODEL_DIRS = [os.getenv("VOSK_MODEL_PATH"), Path("usr/share/vosk"),
        Path.home() / "AppData/Local/vosk", Path.home() / ".cache/vosk"]

parser = argparse.ArgumentParser(
        description = "Transcribe big size audiofiles")
parser.add_argument(
        "--lang", "-l", default="en-us", type=str,
        help="select both model language")
parser.add_argument(
        "--input", "-i", type=str,
        help="audiofile")

def get_model(args):
    for directory in MODEL_DIRS:
        if directory is None or not Path(directory).exists():
            continue
        model_file_list = os.listdir(directory)
        model_files = [model for model in model_file_list if
                re.match(r"vosk-model(-small)?-{}".format(args.lang), model)] 
        if len(model_files) == 2:
            return Path(directory, model_files[0]), Path(directory, model_files[1])

class BigFileProcessor:

    def __init__(self, args, small_model_path, big_model_path):
        self.args = args
        self.queue_in = Queue()
        self.queue_out = Queue()
        self.small_model = Model(model_path=str(small_model_path))
        self.big_model = Model(model_path=str(big_model_path))

    def resample_ffmpeg(self, infile):
        cmd = shlex.split("ffmpeg -nostdin -loglevel quiet "
                "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(infile), SAMPLE_RATE))
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    def process_by_small_model(self):

        rec = KaldiRecognizer(self.small_model, SAMPLE_RATE)
        rec.SetWords(True)
        stream = self.resample_ffmpeg(self.args.input)
        result = []
        data_list = []

        while True:
            data = stream.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                rec.Result()
                result.append(data_list)
                data_list = []
            else:
                rec.PartialResult()
                if data != "b''":
                    data_list.append(data)
        final_result = json.loads(rec.FinalResult())
        if final_result != '':
            result.append(data_list)
        return result

    def process_by_big_model(self, result):
        
        rec = KaldiRecognizer(self.big_model, SAMPLE_RATE)

        for data in self.queue_in.get_nowait():
            if rec.AcceptWaveform(data):
                print(json.loads(rec.Result())["text"])
            else:
                rec.PartialResult()
       
        final_result = json.loads(rec.FinalResult())["text"]
        if final_result != '':
            print(final_result)
        return

    def process(self):

        result = self.process_by_small_model()

        for x in result:
            self.queue_in.put(x)

        with Pool() as pool:
            pool.map(self.process_by_big_model, result)

def main():

    args = parser.parse_args()

    small_model_path, big_model_path = get_model(args)

    processor = BigFileProcessor(args, small_model_path, big_model_path)
    
    processor.process()

if __name__ == "__main__":
    main()
