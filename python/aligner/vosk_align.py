import argparse
import logging
import multiprocessing
import os
import sys
from vosk import aligner, Model

parser = argparse.ArgumentParser(
        description='Align a transcript to audio by generating a new language model.  Outputs JSON')
parser.add_argument(
        '-o', '--output', metavar='output', type=str, 
        help='output filename')
parser.add_argument(
        '--log', default="INFO",
        help='the log level (DEBUG, INFO, WARNING, ERROR, or CRITICAL)')
parser.add_argument(
        'audiofile', type=str,
        help='audio file')
parser.add_argument(
        'txtfile', type=str,
        help='transcript text file')
parser.add_argument(
        'path_model', type=str,
        help='set path to model dir')
args = parser.parse_args()

model_path = args.path_model
model = Model(model_path)

log_level = args.log.upper()
logging.getLogger().setLevel(log_level)

disfluencies = set(['uh', 'um'])

def on_progress(p):
    for k,v in p.items():
        logging.debug("%s: %s" % (k, v))

with open(args.txtfile, encoding="utf-8") as fh:
    txt = fh.read()
    check = txt.split()
    if len(check) > 2:
        transcript = txt
    else:
        print("Not enough words to align, should be 3 or more")
        exit (1)

logging.info("converting audio to 8K sampled wav")

with aligner.resampled(args.audiofile) as wavfile:
    logging.info("starting alignment")
    align = aligner.ForcedAligner(transcript, model)
    result = align.transcribe(wavfile, progress_cb=on_progress, logging=logging)

fh = open(args.output, 'w', encoding="utf-8") if args.output else sys.stdout
fh.write(result.to_json(indent=2))
if args.output:
    logging.info("output written to %s" % (args.output))
print()    
