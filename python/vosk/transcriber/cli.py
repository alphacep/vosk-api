#!/usr/bin/env python3

import logging
import argparse

from pathlib import Path
from vosk import list_models, list_languages
from vosk.transcriber.transcriber import Transcriber

parser = argparse.ArgumentParser(
        description = 'Transcribe audio file and save result in selected format')
parser.add_argument(
        '--model', '-m', type=str,
        help='model path')
parser.add_argument(
        '--list-models', default=False, action='store_true', 
        help='list available models')
parser.add_argument(
        '--list-languages', default=False, action='store_true',
        help='list available languages')
parser.add_argument(
        '--model-name', '-n', type=str,
        help='select model by name')
parser.add_argument(
        '--lang', '-l', default='en-us', type=str,
        help='select model by language')
parser.add_argument(
        '--input', '-i', type=str,
        help='audiofile')
parser.add_argument(
        '--output', '-o', default='', type=str,
        help='optional output filename path')
parser.add_argument(
        '--output-type', '-t', default='txt', type=str,
        help='optional arg output data type')
parser.add_argument(
        '--log-level', default='INFO',
        help='logging level')

def main():

    args = parser.parse_args()
    log_level = args.log_level.upper()
    logging.getLogger().setLevel(log_level)

    if args.list_models == True:
        list_models()
        return

    if args.list_languages == True:
        list_languages()
        return

    if not args.input:
        logging.info('Please specify input file or directory')
        exit(1)

    if not Path(args.input).exists():
        logging.info("File/folder '%s' does not exist, please specify an existing file/directory" % (args.input))
        exit(1)

    transcriber = Transcriber(args)

    if Path(args.input).is_dir():
        transcriber.process_dir(args)
        return
    elif Path(args.input).is_file():
        transcriber.process_file(args)
    else:
        logging.info('Wrong arguments')
        exit(1)

if __name__ == "__main__":
    main()
