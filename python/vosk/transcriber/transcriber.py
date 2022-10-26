import json
import logging
import asyncio
import websockets
import srt
import datetime
import shlex
import subprocess

from vosk import KaldiRecognizer, Model
from queue import Queue
from timeit import default_timer as timer
from multiprocessing.dummy import Pool

CHUNK_SIZE = 4000
SAMPLE_RATE = 16000.0

class Transcriber:

    def __init__(self, args):
        self.model = Model(model_path=args.model, model_name=args.model_name, lang=args.lang)
        self.args = args
        self.queue = Queue()

    def recognize_stream(self, rec, stream):
        tot_samples = 0
        result = []

        while True:
            data = stream.stdout.read(CHUNK_SIZE)

            if len(data) == 0:
                break

            tot_samples += len(data)
            if rec.AcceptWaveform(data):
                jres = json.loads(rec.Result())
                logging.info(jres)
                result.append(jres)
            else:
                jres = json.loads(rec.PartialResult())
                if jres["partial"] != "":
                    logging.info(jres)

        jres = json.loads(rec.FinalResult())
        result.append(jres)

        return result, tot_samples

    async def recognize_stream_server(self, proc):
        async with websockets.connect(self.args.server) as websocket:
            tot_samples = 0
            result = []

            await websocket.send('{ "config" : { "sample_rate" : %f } }' % (SAMPLE_RATE))
            while True:
                data = await proc.stdout.read(CHUNK_SIZE)
                tot_samples += len(data)
                if len(data) == 0:
                    break
                await websocket.send(data)
                jres = json.loads(await websocket.recv())
                logging.info(jres)
                if not "partial" in jres:
                    result.append(jres)
            await websocket.send('{"eof" : 1}')
            jres = json.loads(await websocket.recv())
            logging.info(jres)
            result.append(jres)

            return result, tot_samples


    def format_result(self, result, words_per_line=7):
        processed_result = ""
        if self.args.output_type == "srt":
            subs = []

            for _, res in enumerate(result):
                if not "result" in res:
                    continue
                words = res["result"]

                for j in range(0, len(words), words_per_line):
                    line = words[j : j + words_per_line]
                    s = srt.Subtitle(index=len(subs),
                            content = " ".join([l["word"] for l in line]),
                            start=datetime.timedelta(seconds=line[0]["start"]),
                            end=datetime.timedelta(seconds=line[-1]["end"]))
                    subs.append(s)
            processed_result = srt.compose(subs)

        elif self.args.output_type == "txt":
            for part in result:
                if part["text"] != "":
                    processed_result += part["text"] + "\n"

        elif self.args.output_type == "json":
            monologues = {"schemaVersion":"2.0", "monologues":[], "text":[]}
            for part in result:
                if part["text"] != "":
                    monologue["text"] += part["text"]
            for _, res in enumerate(result):
                if not "result" in res:
                    continue
                monologue = { "speaker": {"id": "unknown", "name": None}, "start": 0, "end": 0, "terms": []}
                monologue["start"] = res["result"][0]["start"]
                monologue["end"] = res["result"][-1]["end"]
                monologue["terms"] = [{"confidence": t["conf"], "start": t["start"], "end": t["end"], "text": t["word"], "type": "WORD" } for t in res["result"]]
                monologues["monologues"].append(monologue)
            processed_result = json.dumps(monologues)
        return processed_result

    def resample_ffmpeg(self, infile):
        cmd = shlex.split("ffmpeg -nostdin -loglevel quiet "
                "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(infile), SAMPLE_RATE))
        stream = subprocess.Popen(cmd, stdout=subprocess.PIPE)
        return stream

    async def resample_ffmpeg_async(self, infile):
        cmd = "ffmpeg -nostdin -loglevel quiet "\
        "-i \'{}\' -ar {} -ac 1 -f s16le -".format(str(infile), SAMPLE_RATE)
        return await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE)

    async def server_worker(self):
        while True:
            try:
                input_file, output_file = self.queue.get_nowait()
            except Exception:
                break

            logging.info("Recognizing {}".format(input_file))
            start_time = timer()
            proc = await self.resample_ffmpeg_async(input_file)
            result, tot_samples = await self.recognize_stream_server(proc)

            processed_result = self.format_result(result)
            if output_file != "":
                logging.info("File {} processing complete".format(output_file))
                with open(output_file, "w", encoding="utf-8") as fh:
                    fh.write(processed_result)
            else:
                print(processed_result)

            await proc.wait()

            elapsed = timer() - start_time
            logging.info("Execution time: {:.3f} sec; "\
                    "xRT {:.3f}".format(elapsed, float(elapsed) * (2 * SAMPLE_RATE) / tot_samples))
            self.queue.task_done()

    def pool_worker(self, inputdata):
        logging.info("Recognizing {}".format(inputdata[0]))
        start_time = timer()

        try:
            stream = self.resample_ffmpeg(inputdata[0])
        except FileNotFoundError as e:
            print(e, "Missing FFMPEG, please install and try again")
            return
        except Exception as e:
            logging.info(e)
            return

        rec = KaldiRecognizer(self.model, SAMPLE_RATE)
        rec.SetWords(True)
        result, tot_samples = self.recognize_stream(rec, stream)
        processed_result = self.format_result(result)

        if inputdata[1] != "":
            logging.info("File {} processing complete".format(inputdata[1]))
            with open(inputdata[1], "w", encoding="utf-8") as fh:
                fh.write(processed_result)
        else:
            print(processed_result)

        elapsed = timer() - start_time
        logging.info("Execution time: {:.3f} sec; "\
                "xRT {:.3f}".format(elapsed, float(elapsed) * (2 * SAMPLE_RATE) / tot_samples))

    async def process_task_list_server(self, task_list):
        for x in task_list:
            self.queue.put(x)
        workers = [asyncio.create_task(self.server_worker()) for i in range(self.args.tasks)]
        await asyncio.gather(*workers)

    def process_task_list_pool(self, task_list):
        with Pool() as pool:
            pool.map(self.pool_worker, task_list)

    def process_task_list(self, task_list):
        if self.args.server is None:
            self.process_task_list_pool(task_list)
        else:
            asyncio.run(self.process_task_list_server(task_list))
