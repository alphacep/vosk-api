#!/usr/bin/env python3

import logging
import argparse

from transcriber import Transcriber as transcriber
from multiprocessing.dummy import Pool
from pathlib import Path


parser = argparse.ArgumentParser(
        description = 'The program transcripts audiofile and displays result in selected format')
parser.add_argument(
        '-model', type=str,
        help='model path')
parser.add_argument(
        '-models_list', default=False, action='store_true', 
        help='list of all models')
parser.add_argument(
        '-model_name',  default='vosk-model-small-en-us-0.15', type=str,
        help='select model current language type')
parser.add_argument(
        '-lang', type=str,
        help='smallest available model for selected language')
parser.add_argument(
        '-input', type=str,
        help='audiofile')
parser.add_argument(
        '-output', default='', type=str,
        help='optional output filename path')
parser.add_argument(
        '-otype', '--outputtype', default='txt', type=str,
        help='optional arg output data type')
parser.add_argument(
        '--log', default='INFO',
        help='logging level')

args = parser.parse_args()
log_level = args.log.upper()
logging.getLogger().setLevel(log_level)
logging.info('checking args')

def get_results(inputdata):
    logging.info('converting audiofile to 16K sampled wav')
    stream = transcriber.resample_ffmpeg(inputdata[0])
    logging.info('complite')
    logging.info('starting transcription')
    final_result, tot_samples = transcriber.transcribe(model, stream, args)
    logging.info('complite')
    if args.output:
        with open(inputdata[1], 'w', encoding='utf-8') as fh:
            fh.write(final_result)
        logging.info('output written to %s' % (inputdata[1]))
    else:
        print(final_result)
    return final_result, tot_samples

def main(args):
    global model
    if args.models_list == True:
        transcriber.models_list()
    if args.input:
        model = transcriber.get_model(args)
        if Path(args.input).is_dir() and Path(args.output).is_dir():
            file_list = transcriber.get_file_list(args)
            with Pool() as pool:
                for final_result, tot_samples in pool.map(get_results, file_list):
                    return final_result, tot_samples
        elif Path(args.input).is_file():
            inputdata = (args.input, args.output)
            final_result, tot_samples = get_results(inputdata)
        return final_result, tot_samples
    else:
        logging.info('Please set input arg')
        exit(1)

if __name__ == '__main__':
    start_time = transcriber.get_start_time()
    tot_samples = main(args)[1]
    diff_end_start, sec, mcsec = transcriber.get_end_time(start_time)
    logging.info(f'''Script info: execution time: {sec} sec, {mcsec} mcsec; xRT: {format(tot_samples / 16000.0 / float(diff_end_start), '.3f')}''')
