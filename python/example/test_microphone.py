#!/usr/bin/env python3

# prerequisites: as described in https://alphacephei.com/vosk/install and also python module `sounddevice` (simply run command `pip install sounddevice`)
# Example usage using Dutch (nl) recognition model: `python test_microphone.py -m nl`
# For more help run: `python test_microphone.py -h`

import argparse
from dataclasses import dataclass
import json
import queue
import sys
import sounddevice as sd
from typing import Any, Tuple

from vosk import Model, KaldiRecognizer

DEFAULT_ALTERNATIVES = 10

q = queue.Queue()

def int_or_str(text):
    """Helper function for argument parsing."""
    try:
        return int(text)
    except ValueError:
        return text

def callback(indata, frames, time, status):
    """This is called (from a separate thread) for each audio block."""
    if status:
        print(status, file=sys.stderr)
    q.put(bytes(indata))

parser = argparse.ArgumentParser(
    add_help=False,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter,
)
parser.add_argument(
    "-l", "--list-devices", action="store_true",
    help="show list of audio devices and exit")
args, remaining = parser.parse_known_args()
if args.list_devices:
    print(sd.query_devices())
    parser.exit(0)
parser = argparse.ArgumentParser(
    description=__doc__,
    formatter_class=argparse.RawDescriptionHelpFormatter,
    parents=[parser])
parser.add_argument(
    "-f", "--filename", type=str, metavar="FILENAME",
    help="audio file to store recording to")
parser.add_argument(
    "-d", "--device", type=int_or_str,
    help="input device (numeric ID or substring)")
parser.add_argument(
    "-r", "--samplerate", type=int, help="sampling rate")
parser.add_argument(
    "-m", "--model", type=str, help="language model; e.g. en-us, fr, nl; default is en-us")
parser.add_argument(
    "-se", "--skip-empty", action="store_true", help="Skip empty partial results.")
parser.add_argument(
    "--alternatives", type=int, nargs="?", const=DEFAULT_ALTERNATIVES, help=f"Generate N alternatives ({DEFAULT_ALTERNATIVES} by default) with confidence instead of single result.")
parser.add_argument(
    "--nlsml", action="store_true", help="Generate output in NLSML (Natural Language Semantics Markup Language). Disables pretty print. Implies alternatives generation.")
parser.add_argument(
    "-pp", "--prettyprint", action="store_true", help="Enable pretty (less verbose) output")
args = parser.parse_args(remaining)

try:
    if args.samplerate is None:
        device_info = sd.query_devices(args.device, "input")
        # soundfile expects an int, sounddevice provides a float:
        args.samplerate = int(device_info["default_samplerate"])
        
    if args.model is None:
        model = Model(lang="en-us")
    else:
        model = Model(lang=args.model)

    if args.filename:
        dump_fn = open(args.filename, "wb")
    else:
        dump_fn = None

    alternatives = args.alternatives
    if not alternatives and args.nlsml:
        alternatives = DEFAULT_ALTERNATIVES
    
    pretty_print = args.prettyprint

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        if alternatives:
            rec.SetMaxAlternatives(alternatives)

        if args.nlsml:
            rec.SetNLSML(True)
            pretty_print = False

        need_newline = False
        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                result = rec.Result()
            else:
                result = rec.PartialResult()

            if dump_fn is not None:
                dump_fn.write(data)

            try:
                result_dict = json.loads(result)
            except:
                result_dict = {}

            if args.skip_empty and result_dict.get("partial") == "":
                continue

            if pretty_print:
                if result_dict.get("partial") == "":
                    print(".", end="", flush=True)
                    need_newline = True
                else:
                    if need_newline:
                        print()
                        need_newline = False
                    if partial := result_dict.get("partial"):
                        print(f"> {partial}")
                    elif text := result_dict.get("text"):
                        print(f"# {text}")
                    elif alternatives := result_dict.get("alternatives"):
                        for idx, alternative in enumerate(alternatives):
                            print(f"# {idx + 1:2}. {alternative["confidence"]:3.2f} {alternative["text"]}")
            else:
                print(result)
            

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))
