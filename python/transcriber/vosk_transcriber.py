import os
import logging
import sys
import argparse

from transcriber import Transcriber as transcriber
from vosk import Model
from multiprocessing.dummy import Pool


parser = argparse.ArgumentParser(
        description = 'The program transcripts audiofile and displays result in selected format')
parser.add_argument(
        'model', type=str,
        help='model path')
parser.add_argument(
        '-i', '--input', type=str,
        help='optional arg audiofile')
parser.add_argument(
        '-o', '--output', metavar='outputdata', type=str,
        help='output filename path')
parser.add_argument(
        '-ot', '--outputtype', type=str,
        help='output data type without dot')
parser.add_argument(
        '--log', default='INFO',
        help='logging level')

args = parser.parse_args()
log_level = args.log.upper()
logging.getLogger().setLevel(log_level)
logging.info('checking input args')

def calculate(model, inputdata, outputdata, outputtype, log):
    logging.info('converting audiofile to 16K sampled wav')
    wf = transcriber.resample_ffmpeg(inputdata)
    logging.info('converting complite')
    logging.info('startting transcription')
    final_result, tot_samples = transcriber.transcribe(model, wf)
    logging.info('transcription complite')
    fh = open(outputdata, 'w', encoding='utf-8') if outputdata else sys.stdout
    fh.write(final_result)
    if outputdata:
        logging.info('output writen to %s' % (outputdata))
    logging.info('program finished')

    return final_result, tot_samples

def main(model, inputdata, outputdata, outputtype, log):
    logging.info('checking model')
    model = Model('model')
    if not os.path.exists('model'):
        print("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")
    
    if os.path.isdir(inputdata) and os.path.isdir(outputdata) and outputtype:
        arg_list = transcriber.process_dirs(model, inputdata, outputdata, outputtype, log)
        with Pool() as pool:
            for final_result, tot_samples in pool.starmap(calculate, arg_list):
                return final_result, tot_samples
    
    elif os.path.isfile(inputdata):
        final_result, tot_samples = calculate(model, inputdata, outputdata, outputtype, log)
    return final_result, tot_samples

if __name__ == '__main__':
    start_time = transcriber.get_time()
    tot_samples = main(args.model, args.input, args.output, args.outputtype, args.log)[1]
    diff_end_start, sec, mcsec = transcriber.send_time(start_time)
    print('\n'f'''Script info: execution time: {sec} sec, {mcsec} mcsec; xRT: {format(tot_samples / 16000.0 / float(diff_end_start), '.3f')}''')
