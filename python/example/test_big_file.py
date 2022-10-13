#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import json
import shlex
import srt
import datetime

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
parser.add_argument(
        "--output", "-o", default="txt", type=str,
        help="output type")

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
        self.queue = Queue()
        self.small_model = Model(model_path=str(small_model_path))
        self.big_model = Model(model_path=str(big_model_path))

    def resample_ffmpeg(self):
        cmd = shlex.split("ffmpeg -nostdin -loglevel quiet "
                "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(self.args.input), SAMPLE_RATE))
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    def prepare_audio_fragments(self):
        rec = KaldiRecognizer(self.small_model, SAMPLE_RATE)
        rec.SetWords(True)
        stream = self.resample_ffmpeg()
        result = []
        data_list = []

        while True:
            data = stream.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())
                if "result" in res.keys():
                    result.append(data_list)
                    data_list = []
            else:
                rec.PartialResult()
                if data != "b''":
                    data_list.append(data)
        
        res = json.loads(rec.FinalResult())
        if "result" in res.keys():
            result.append(data_list)
        return result

    def get_srt_result(self, data_list, words_per_line = 7):
        rec = KaldiRecognizer(self.big_model, SAMPLE_RATE)
        rec.SetWords(True)
        results = []
        result = []
        
        for data in data_list:
            if rec.AcceptWaveform(data):
                results.append(rec.Result())
        results.append(rec.FinalResult())

        subs = []
        for res in results:
            jres = json.loads(res)
            if not "result" in jres:
                continue
            words = jres["result"]
            for j in range(0, len(words), words_per_line):
                line = words[j : j + words_per_line]
                s = srt.Subtitle(index=len(subs),
                        content=" ".join([l["word"] for l in line]),
                        start=datetime.timedelta(seconds=line[0]["start"]),
                        end=datetime.timedelta(seconds=line[-1]["end"]))
                subs.append(s)
        result.append(srt.compose(subs))
        return result

    def get_txt_result(self, data_list):
        rec = KaldiRecognizer(self.big_model, SAMPLE_RATE)
        result = []
        for data in data_list:
            if rec.AcceptWaveform(data):
                res = json.loads(rec.Result())["text"]
                result.append(res)
            else:
                rec.PartialResult()
        res = json.loads(rec.FinalResult())["text"]
        result.append(res)
        return result

    def process_by_big_model(self, data):
        if self.args.output == "txt":
            result = self.get_txt_result(data)
        else:
            result = self.get_srt_result(data)
        return result

    def process(self):

        total_result = self.prepare_audio_fragments()
        with Pool() as pool:
            for phrase in pool.map(self.process_by_big_model, total_result):
                for each in phrase:
                    print(phrase[0])

def main():

    args = parser.parse_args()

    small_model_path, big_model_path = get_model(args)

    processor = BigFileProcessor(args, small_model_path, big_model_path)
    
    processor.process()

if __name__ == "__main__":
    main()
