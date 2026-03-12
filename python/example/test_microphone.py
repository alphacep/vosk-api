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
from typing import Any

from vosk import Model, KaldiRecognizer

q = queue.Queue()

@dataclass(kw_only=True)
class Result:
    text: str
    is_partial: bool
    raw: Any

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

parser = argparse.ArgumentParser(add_help=False)
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
    "--nlsml", action="store_true", help="Generate output in NLSML (Natural Language Semantics Markup Language). Disables pretty print.")
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

    pretty_print = args.prettyprint

    with sd.RawInputStream(samplerate=args.samplerate, blocksize = 8000, device=args.device,
            dtype="int16", channels=1, callback=callback):
        print("#" * 80)
        print("Press Ctrl+C to stop the recording")
        print("#" * 80)

        rec = KaldiRecognizer(model, args.samplerate)
        if args.nlsml:
            rec.SetMaxAlternatives(10)
            rec.SetNLSML(True)
            pretty_print = False

        while True:
            data = q.get()
            if rec.AcceptWaveform(data):
                raw_result = rec.Result()
                try:
                    result_json = json.loads(raw_result)
                except:
                    result_json = None

                result = Result(
                    is_partial=False,
                    raw=raw_result,
                    text=result_json["text"] if result_json else "", 
                )
            else:
                raw_result = rec.PartialResult()
                result_json = json.loads(raw_result)                
                result = Result(
                    is_partial=True,
                    raw=raw_result,
                    text=result_json["partial"], 
                )

            if dump_fn is not None:
                dump_fn.write(data)

            if args.skip_empty and result.is_partial and not result.text:
                continue

            if pretty_print:
                if result.is_partial and not result.text:
                    print(".", end="", flush=True)
                else:
                    print("> " if result.is_partial else "# ", end="")
                    print(result.text)
            else:
                print(result.raw)
            

except KeyboardInterrupt:
    print("\nDone")
    parser.exit(0)
except Exception as e:
    parser.exit(type(e).__name__ + ": " + str(e))
