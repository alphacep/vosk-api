import argparse
import logging
import wave
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
        'model', type=str,
        help='set path to model dir')

def main(audiofile, txtfile, model, output):
    model = Model(model)

    def on_progress(p):
        for k,v in p.items():
            logging.debug("%s: %s" % (k, v))

    with open(txtfile, encoding="utf-8") as fh:
        transcript = fh.read()

    with wave.open(audiofile) as wavfile:
        logging.info("starting alignment")
        align = aligner.ForcedAligner(transcript, model)
        result = align.transcribe(wavfile, progress_cb=on_progress, logging=logging)
    final_result = ((result.to_json(indent=2)).replace(',\n      "realign": false,', ',')) 
    fh = open(output, 'w', encoding="utf-8") if output else sys.stdout
    fh.write(final_result)
    if output:
        logging.info("output written to %s" % (output))
    print()

if __name__ == "__main__":
    args = parser.parse_args()
    main(args.audiofile, args.txtfile, args.model, args.output)
