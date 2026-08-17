#!/usr/bin/env python3

import argparse
import logging
import wave
import sys

from vosk import Model
from vosk.aligner import scripts

parser = argparse.ArgumentParser(
        description='Align a transcript to audio by generating a new language model.  Outputs JSON')
parser.add_argument(
        'audiofile', type=str,
        help='path to audio file')
parser.add_argument(
        'txtfile', type=str,
        help='path to text file')
parser.add_argument(
        'model', type=str,
        help='path to model directory')
parser.add_argument(
        '-o', '--output', metavar='output', type=str, 
        help='output filename')
parser.add_argument(
        '--log', default="INFO",
        help='the log level (DEBUG, INFO, WARNING, ERROR, or CRITICAL)')

def get_result(args):

    def on_progress(p):
        for k,v in p.items():
            logging.debug("%s: %s" % (k, v))

    with open(args.txtfile, encoding="utf-8") as fh:
        transcript = fh.read() 
    model = Model(args.model)
    with wave.open(args.audiofile) as wavfile:
        logging.info("starting alignment")
        align = scripts.ForcedAligner(transcript, model)
        intermediate_result = align.transcribe(wavfile, progress_cb=on_progress, logging=logging)
    result = ((intermediate_result.to_json(indent=2)).replace(',\n      "realign": false,', ','))
    fh = open(args.output, 'w', encoding="utf-8") if args.output else sys.stdout
    fh.write(result)
    if args.output:
        logging.info("output written to %s" % (args.output))
    print()
    return result

def main():

    args=parser.parse_args()
    log_level = args.log.upper()
    logging.getLogger().setLevel(log_level) 
    get_result(args)

if __name__ == "__main__":
    main()
