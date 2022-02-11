import os
import wave
import logging
import sys
import argparse

from transcriber import Transcriber as transcriber
from vosk import Model


parser = argparse.ArgumentParser(
        description = 'The program transcripts audiofile and displays result in selected format')
parser.add_argument(
        'model', type=str,
        help='model path')
parser.add_argument(
        '-i', '--input', metavar='inputfile', type=str,
        help='optional arg audiofile')
parser.add_argument(
        '-o', '--output', metavar='outputfile', type=str,
        help='output filename path')
parser.add_argument(
        '-d', '--folder', type=str,
        help='optional arg input folder with audiofiles')
parser.add_argument(
        '-od', '--output folder', type=str,
        help='optional arg output folder with transcription files')
parser.add_argument(
        '--log', default='INFO',
        help='logging level')

args = parser.parse_args()
log_level = args.log.upper()
logging.getLogger().setLevel(log_level)
logging.info('checking input args')

def main(model, inputfile, outputfile, options, log):
    
    logging.info('checking model')
    if not os.path.exists('model'):
        print("Please download the model from https://alphacephei.com/vosk/models and unpack as 'model' in the current folder.")

    model = Model('model') 
    logging.info('converting audiofile to 16K sampled wav')
    wf = transcriber.resample_ffmpeg(inputfile)
    logging.info('converting complite')
    logging.info('starting transcription')
    final_result, tot_samples = transcriber.transcribe(model, wf)
    logging.info('transcription complite')
    fh = open(outputfile, 'w', encoding='utf-8') if outputfile else sys.stdout
    fh.write(final_result)

    if outputfile:
        logging.info('output written to %s' % (outputfile))        
    logging.info('program finished')
    return final_result, tot_samples

if __name__ == '__main__':
    start_time = transcriber.get_time()
    tot_samples = main(args.model, args.input, args.output, args.folder, args.log)[1]
    diff_end_start, sec, mcsec = transcriber.send_time(start_time)
    print('\n'f'''Script info: execution time: {sec} sec, {mcsec} mcsec; xRT: {format(tot_samples / 16000.0 / float(diff_end_start), '.3f')}''')
