#!/usr/bin/env python3

import os
import argparse
import json
import sys
import shlex
import subprocess
import logging
import srt
import datetime

from pathlib import Path
from re import split
from vosk import Model, KaldiRecognizer, SetLogLevel, list_model_pairs, list_models, list_languages
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
        help="language")
parser.add_argument(
        "--small", "-s", default="vosk-model-small-en-us-0.15", type=str,
        help="small model name")
parser.add_argument(
        "--big", "-b", default="vosk-model-en-us-0.22", type=str,
        help="big model name")
parser.add_argument(
        "--input", "-i", type=str,
        help="audiofile")
parser.add_argument(
        "--output", "-o", default="txt", type=str,
        help="output type")
parser.add_argument(
        "--list-models", default=False, action="store_true",
        help="list available models")
parser.add_argument(
        "--list-languages", default=False, action="store_true",
        help="list available languages")
parser.add_argument(
        "--list-model-pairs", default=False, action="store_true",
        help="list available model pairs")
parser.add_argument(
        "--log-level", default="INFO",
        help="logging level")

class BigFileProcessor:

    def __init__(self, args):
        self.args = args
        self.small_model = Model(model_name=str(args.small))
        self.big_model = Model(model_name=str(args.big))

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
            return srt.compose(subs)
        else:
            return json.loads(results[0])["text"]

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

    if args.list_model_pairs:
        list_model_pairs(args.lang)
        return

    if args.list_models:
        list_models()
        return

    if args.list_languages:
        list_languages()
        return

    if not args.input:
        logging.info("Please specify input file")
        sys.exit(1)

    small_model_lang = split(r"(-\d.+)", split(r"vosk-model-(small-)*", args.small)[-1])[0]
    big_model_lang = split(r"(-\d.+)", split(r"vosk-model-(small-)*", args.big)[-1])[0]
    if not small_model_lang == big_model_lang:
        logging.info("You have to use both models for the same language, try again.")
        sys.exit(1)

    if args.output not in ["txt", "srt"]:
        logging.info("Wrong output format, it has to be txt(by default) or srt as optional, "\
        "please try again.")
        sys.exit(1)

    processor = BigFileProcessor(args)

    start_time = timer()

    logging.info("File processing started")
    processor.process_file()

    elapsed = timer() - start_time
    logging.info("Execution time: {:.3f}".format(elapsed))

if __name__ == "__main__":
    main()
