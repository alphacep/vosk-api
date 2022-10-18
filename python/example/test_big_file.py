#!/usr/bin/env python3

import os
import argparse
import requests
import json
import sys
import shlex
import subprocess
import logging
import srt
import datetime

from pathlib import Path
from tqdm import tqdm
from urllib.request import urlretrieve
from zipfile import ZipFile
from re import match
from vosk import Model, KaldiRecognizer, SetLogLevel, list_languages
from multiprocessing.dummy import Pool
from timeit import default_timer as timer

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
parser.add_argument(
        "--list-languages", default=False, action="store_true",
        help="list available languages")

def download_progress_hook(t):
    last_b = [0]
    def update_to(b=1, bsize=1, tsize=None):
        if tsize not in (None, -1):
            t.total = tsize
        displayed = t.update((b - last_b[0]) * bsize)
        last_b[0] = b
        return displayed
    return update_to

def download_model(small_model_path, big_model_path):
    if not (small_model_path.parent).exists():
        (small_model_path.parent).mkdir(parents=True)
    model_names = [small_model_path, big_model_path]
    for model_name in model_names:
        if model_name.exists():
            continue
        with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1,
                desc=(MODEL_PRE_URL + str(model_name.name) + ".zip").rsplit("/",
                    maxsplit=1)[-1]) as t:
            reporthook = download_progress_hook(t)
            urlretrieve(MODEL_PRE_URL + str(model_name.name) + ".zip",
                    str(model_name) + ".zip", reporthook=reporthook, data=None)
            t.total = t.n
            with ZipFile(str(model_name) + ".zip", "r") as model_ref:
                model_ref.extractall(model_name.parent)
            Path(str(model_name) + ".zip").unlink()

def get_models(args):
    for directory in MODEL_DIRS:
        if directory is None or not Path(directory).exists():
            continue
        model_file_list = os.listdir(directory)
        small_model_file = [model for model in model_file_list if
                match(r"vosk-model-small-{}".format(args.lang), model)]
        big_model_file = [model for model in model_file_list if
                match(r"vosk-model-{}".format(args.lang), model)]
        if small_model_file != [] and big_model_file != []:
            return Path(directory, small_model_file[0]), Path(directory, big_model_file[0])
    response = requests.get(MODEL_LIST_URL, timeout=10)
    result_small_model = [model["name"] for model in response.json() if
            model["lang"] == args.lang and model["type"] == "small" and
            model["obsolete"] == "false"]
    result_big_model = [model["name"] for model in response.json() if
            model["lang"] == args.lang and model["type"] == "big" and
            model["obsolete"] == "false"]
    if result_small_model == [] or result_big_model == []:
        print("lang %s does not exist" % (args.lang))
        sys.exit(1)
    else:
        download_model(Path(directory, result_small_model[0]), Path(directory, result_big_model[0]))
        return Path(directory, result_small_model[0]), Path(directory, result_big_model[0])

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
        logging.info("Process file fragment")
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
        logging.info("File fragments are ready")
        with Pool() as pool:
            for fragment in pool.map(self.format_result, fragments):
                print(fragment)

def main():

    args = parser.parse_args()
    log_level = args.log_level.upper()
    logging.getLogger().setLevel(log_level)

    if args.list_languages is True:
        list_languages()
        return
    
    if not args.input:
        logging.info("Please specify input file")
        sys.exit(1)

    if args.output not in ["txt", "srt"]:
        logging.info("Wrong output format, it has to be txt(by default) or srt as optional, "\
        "please try again.")
        sys.exit(1)

    small_model_path, big_model_path = get_models(args)
    logging.info("Models are ready")

    processor = BigFileProcessor(args, small_model_path, big_model_path)

    start_time = timer()

    logging.info("File processing started")
    processor.process_file()

    elapsed = timer() - start_time
    logging.info("Execution time: {:.3f}".format(elapsed))

if __name__ == "__main__":
    main()
