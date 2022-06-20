import json
import subprocess
import srt
import datetime
import os
import logging
import asyncio
import websockets
import shutil

from pathlib import Path
from timeit import default_timer as timer
from vosk import KaldiRecognizer, Model
from multiprocessing.dummy import Pool

class Transcriber:

    def __init__(self, args):
        self.model = Model(model_path=args.model, model_name=args.model_name, lang=args.lang)
        self.args = args

    def recognize_stream(self, rec, stream):
        tot_samples = 0
        result = []
        while True:
            data = stream.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                tot_samples += len(data)
                result.append(json.loads(rec.Result()))
                logging.info('Processing...')
        result.append(json.loads(rec.FinalResult()))
        return result, tot_samples

    def format_result(self, result, words_per_line=7):
        final_result = ''
        if self.args.output_type == 'srt':
            subs = []
            for i, res in enumerate(result):
                if not 'result' in res:
                    continue
                words = res['result']
                for j in range(0, len(words), words_per_line):
                    line = words[j : j + words_per_line]
                    s = srt.Subtitle(index=len(subs),
                            content = ' '.join([l['word'] for l in line]),
                            start=datetime.timedelta(seconds=line[0]['start']),
                            end=datetime.timedelta(seconds=line[-1]['end']))
                    subs.append(s)
            final_result = srt.compose(subs)
        elif self.args.output_type == 'txt':
            for part in result:
                final_result += part['text'] + ' '
        return final_result

    async def run_test(self, uri, stream):
        async with websockets.connect(uri) as websocket:
            await websocket.send('{ "config" : { "sample_rate" : %d } }' % 16000)
            result = []
            tot_samples = 0
            while True:
                data = stream.stdout.read(4000)
                if len(data) == 0:
                    break
                await websocket.send(data)
                tot_samples += len(data)
                results = json.loads(await websocket.recv())
                if not 'partial' in results:
                    result.append(results)
                logging.info('Processing...')
            await websocket.send('{"eof" : 1}')
            result.append(json.loads(await websocket.recv()))
        return result, tot_samples

    def resample_ffmpeg(self, infile):
        stream = subprocess.Popen(
            ['ffmpeg', '-nostdin', '-loglevel', 'quiet', '-i', 
            infile, 
            '-ar', '16000','-ac', '1', '-f', 's16le', '-'], 
            stdout=subprocess.PIPE)
        return stream


    def process_entry(self, inputdata):
        logging.info(f'Recognizing {inputdata[0]}')

        rec = KaldiRecognizer(self.model, 16000)
        rec.SetWords(True)
        
        if shutil.which("ffmpeg"):
            stream = self.resample_ffmpeg(inputdata[0])
        else:
            logging.info('Missing ffmpeg, please install and try again')
            exit(1)

        if self.args.server is None:
            intermediate_result, tot_samples = self.recognize_stream(rec, stream)
        else:
            intermediate_result, tot_samples = asyncio.run(self.run_test('ws://' + self.args.server, stream))
        
        result = []
        for i, res in enumerate(intermediate_result):
            if not 'partial' in res.keys():
                result.append(res)

        final_result = self.format_result(result)

        if inputdata[1] != '':
            logging.info(f'Writing processing result to %s' % (inputdata[1]))
            with open(inputdata[1], 'w', encoding='utf-8') as fh:
                fh.write(final_result)
        else:
            print(final_result)
        return final_result, tot_samples

    def process_dir(self, args):
        task_list = [(Path(args.input, fn), Path(args.output, Path(fn).stem).with_suffix('.' + args.output_type)) for fn in os.listdir(args.input)]
        with Pool() as pool:
            pool.map(self.process_entry, task_list)

    def process_file(self, args):
        start_time = timer()
        final_result, tot_samples = self.process_entry([args.input, args.output])
        elapsed = timer() - start_time
        logging.info(f'''Execution time: {elapsed:.3f} sec; xRT: {format(tot_samples / 16000.0 / float(elapsed), '.3f')}''')
