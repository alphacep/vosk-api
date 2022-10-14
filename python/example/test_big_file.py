#!/usr/bin/env python3

import argparse
import os
import re
import subprocess
import json
import shlex
import srt
import datetime
import logging
import sys

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
parser.add_argument(
        "--log-level", default="INFO",
        help="logging level")

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
        self.small_model = Model(model_path=str(small_model_path))
        self.big_model = Model(model_path=str(big_model_path))

    def resample_ffmpeg(self):
        cmd = shlex.split("ffmpeg -nostdin -loglevel quiet "
                "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(self.args.input), SAMPLE_RATE))
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    def prepare_fragments(self):
        rec = KaldiRecognizer(self.small_model, SAMPLE_RATE)
        stream = self.resample_ffmpeg()
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
                data_list.append(data)
        if json.loads(rec.FinalResult())["text"] != "":
            result.append(data_list)
        return result

    def format_result(self, data_list, words_per_line = 7):
        logging.info("Process file fragment...")
        rec = KaldiRecognizer(self.big_model, SAMPLE_RATE)
        rec.SetWords(True)
        results = []
        result = []
        
        for data in data_list:
            if rec.AcceptWaveform(data):
                results.append(rec.Result())
        results.append(rec.FinalResult())
        if self.args.output == "srt":
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
        else:
            return json.loads(results[0])["text"]
        return result[0]

    def process_file(self):
        fragments = self.prepare_fragments()
        logging.info("File fragments ready")
        with Pool() as pool:
            for fragment in pool.map(self.format_result, fragments):
                print(fragment)

def main():

    args = parser.parse_args()
    log_level = args.log_level.upper()
    logging.getLogger().setLevel(log_level)

    if args.output not in ["txt", "srt"]:
        logging.info("Wrong output format, it has to be txt(by default) or srt as optional, please try again.")
        sys.exit(1)

    small_model_path, big_model_path = get_model(args)

    processor = BigFileProcessor(args, small_model_path, big_model_path)
    
    processor.process_file()

if __name__ == "__main__":
    main()
