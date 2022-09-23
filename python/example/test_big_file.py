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
parser.add_argument(
        "--cores", "-c", default=4, type=int,
        help="PC cores used for recognize")

class HugeFileProcessor:

    def __init__(self, args):
        self.args = args
        self.queue = Queue()

    def resample_ffmpeg(self, infile):
        cmd = shlex.split("ffmpeg -nostdin -loglevel quiet "
                "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(infile), SAMPLE_RATE))
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    def get_model(self):
        for directory in MODEL_DIRS:
            if directory is None or not Path(directory).exists():
                continue
            model_file_list = os.listdir(directory)
            model_files = [model for model in model_file_list if
                    re.match(r"vosk-model(-small)?-{}".format(self.args.lang), model)] 
            if len(model_files) == 2:
                return Path(directory, model_files[0]), Path(directory, model_files[1])

    def process_by_small_model(self, small_model_path):

        model = Model(model_path=str(small_model_path))
        rec = KaldiRecognizer(model, SAMPLE_RATE)
        rec.SetPartialWords(True)
        fragments = []

        stream = self.resample_ffmpeg(self.args.input)

        while True:
            data = stream.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                rec.Result()
                if part_res["partial"] != '' and part_res["partial_result"] != '':
                    fragments.append((int(part_res["partial_result"][0]["start"]),
                            int(part_res["partial_result"][-1]["end"])))
            else:
                part_res = json.loads(rec.PartialResult())
        rec.FinalResult()
        return fragments

    def process_by_big_model(self, timestamps):

        item_0, item_1 = self.queue.get_nowait()

        model = Model(model_path=str(big_model_path))
        rec = KaldiRecognizer(model, SAMPLE_RATE)
        start_pos = 32000 * item_0
        end_pos = 32000 * item_1

        stream = self.resample_ffmpeg(self.args.input)
        stream.stdout.read(start_pos)

        while True:
            data = stream.stdout.read(4000)
            if end_pos - start_pos == 0:
                break
            if rec.AcceptWaveform(data):
                rec.Result()
            else:
                print(rec.PartialResult())
            start_pos += 4000
        print(rec.FinalResult())
        return

    def process(self, small_model_path):

        timestamps = self.process_by_small_model(small_model_path)
        
        for x in timestamps:
            self.queue.put(x)

        with Pool(self.args.cores) as pool:
            pool.map(self.process_by_big_model, timestamps)

def main():

    args = parser.parse_args()

    processor = HugeFileProcessor(args)
    global big_model_path
    small_model_path, big_model_path = processor.get_model()

    processor.process(small_model_path)

if __name__ == "__main__":
    main()
