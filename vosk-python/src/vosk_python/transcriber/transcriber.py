"""
Defines the Transcriber class, which handles the core logic for audio transcription.

It supports both local and server-based recognition, file resampling, and formatting of the output
in various formats like plain text, SRT, and JSON.
"""

import argparse
import asyncio
import datetime
import json
import logging
import shlex
import subprocess
from multiprocessing.dummy import Pool
from pathlib import Path
from queue import Queue
from timeit import default_timer as timer
from typing import Any

import srt
import websockets
from vosk_python import KaldiRecognizer, Model

logger = logging.getLogger(__name__)

CHUNK_SIZE: int = 4000
SAMPLE_RATE: float = 16000.0


class Transcriber:
	"""
	A class to transcribe audio files using the Vosk library.

	This class manages the transcription process, including model loading, audio resampling,
	and formatting of the recognition results.
	"""

	def __init__(self, args: argparse.Namespace) -> None:
		"""
		Initializes the Transcriber with given arguments.

		Args:
			args: Command-line arguments providing configuration for the transcriber.

		"""
		self.model: Model = Model(model_path=args.model, model_name=args.model_name, lang=args.lang)
		self.args: argparse.Namespace = args
		self.queue: Queue[tuple[Path, Path | str]] = Queue()

	@staticmethod
	def recognize_stream(rec: KaldiRecognizer, stream: subprocess.Popen) -> tuple[list[dict[str, Any]], int]:
		"""
		Recognizes audio from a stream using a KaldiRecognizer.

		Args:
			rec: The KaldiRecognizer instance.
			stream: A subprocess Popen object representing the audio stream.

		Returns:
			A tuple containing the list of recognition results and the total number of samples processed.

		"""
		tot_samples: int = 0
		result: list[dict[str, Any]] = []

		if stream.stdout is None:
			raise ValueError("Stream stdout is not available.")

		while True:
			data: bytes
			if stream.stdout is None:
				raise ValueError("Stream stdout is not available.")
			data = stream.stdout.read(CHUNK_SIZE)

			if len(data) == 0:
				break

			tot_samples += len(data)
			if rec.accept_waveform(data):
				jres: dict[str, Any] = json.loads(rec.result())
				logger.info(jres)
				result.append(jres)
			else:
				jres = json.loads(rec.partial_result())
				if jres.get("partial", "") != "":
					logger.info(jres)

		jres = json.loads(rec.final_result())
		result.append(jres)

		return result, tot_samples

	async def recognize_stream_server(self, proc: asyncio.subprocess.Process) -> tuple[list[dict[str, Any]], int]:
		"""
		Recognizes audio from a stream using a WebSocket server.

		Args:
			proc: An asyncio subprocess Process object for the audio stream.

		Returns:
			A tuple containing the list of recognition results and the total number of samples processed.

		"""
		async with websockets.connect(self.args.server) as websocket:  # type: ignore
			tot_samples: int = 0
			result: list[dict[str, Any]] = []

			await websocket.send(f'{{ "config" : {{ "sample_rate" : {SAMPLE_RATE} }} }}')
			while True:
				data: bytes = await proc.stdout.read(CHUNK_SIZE)  # type: ignore
				tot_samples += len(data)
				if len(data) == 0:
					break
				await websocket.send(data)
				jres: dict[str, Any] = json.loads(await websocket.recv())
				logger.info(jres)
				if "partial" not in jres:
					result.append(jres)

			await websocket.send('{"eof" : 1}')
			jres = json.loads(await websocket.recv())
			logger.info(jres)
			result.append(jres)

			return result, tot_samples

	def format_result(self, result: list[dict[str, Any]], words_per_line: int = 7) -> str:
		"""
		Formats the recognition result into the specified output type.

		Args:
			result: A list of recognition result dictionaries.
			words_per_line: The number of words per line for SRT output.

		Returns:
			The formatted result as a string.

		"""
		processed_result: str = ""
		if self.args.output_type == "srt":
			subs: list[srt.Subtitle] = []

			for _, res in enumerate(result):
				if "result" not in res:
					continue
				words: list[dict[str, Any]] = res["result"]

				for j in range(0, len(words), words_per_line):
					line: list[dict[str, Any]] = words[j : j + words_per_line]
					s = srt.Subtitle(
						index=len(subs),
						content=" ".join([word["word"] for word in line]),
						start=datetime.timedelta(seconds=line[0]["start"]),
						end=datetime.timedelta(seconds=line[-1]["end"]),
					)
					subs.append(s)
			processed_result = srt.compose(subs)

		elif self.args.output_type == "txt":
			for part in result:
				if part.get("text", "") != "":
					processed_result += part["text"] + "\n"

		elif self.args.output_type == "json":
			monologues: dict[str, Any] = {"schemaVersion": "2.0", "monologues": [], "text": []}
			for part in result:
				if part.get("text", "") != "":
					monologues["text"].append(part["text"])
			for _, res in enumerate(result):
				if "result" not in res:
					continue
				monologue: dict[str, Any] = {
					"speaker": {"id": "unknown", "name": None},
					"start": 0,
					"end": 0,
					"terms": [],
				}
				monologue["start"] = res["result"][0]["start"]
				monologue["end"] = res["result"][-1]["end"]
				monologue["terms"] = [
					{
						"confidence": t["conf"],
						"start": t["start"],
						"end": t["end"],
						"text": t["word"],
						"type": "WORD",
					}
					for t in res["result"]
				]
				monologues["monologues"].append(monologue)
			processed_result = json.dumps(monologues)

		return processed_result

	def resample_ffmpeg(self, infile: Path) -> subprocess.Popen:
		"""
		Resamples an audio file using FFmpeg.

		Args:
			infile: The path to the input audio file.

		Returns:
			A subprocess Popen object for the resampled audio stream.

		"""
		cmd: list[str] = shlex.split(
			f"ffmpeg -nostdin -loglevel quiet -i '{infile!s}' -ar {SAMPLE_RATE} -ac 1 -f s16le -",
		)
		return subprocess.Popen(cmd, stdout=subprocess.PIPE)

	async def resample_ffmpeg_async(self, infile: Path) -> asyncio.subprocess.Process:
		"""
		Asynchronously resamples an audio file using FFmpeg.

		Args:
			infile: The path to the input audio file.

		Returns:
			An asyncio subprocess Process object for the resampled audio stream.

		"""
		cmd: str = f"ffmpeg -nostdin -loglevel quiet -i '{infile!s}' -ar {SAMPLE_RATE} -ac 1 -f s16le -"
		return await asyncio.create_subprocess_shell(cmd, stdout=subprocess.PIPE)

	async def server_worker(self) -> None:
		"""
		A worker that processes transcription tasks from the queue using a WebSocket server.
		"""
		while True:
			try:
				input_file, output_file = self.queue.get_nowait()
			except Exception:
				break

			logger.info(f"Recognizing {input_file}")
			start_time: float = timer()
			proc: asyncio.subprocess.Process = await self.resample_ffmpeg_async(input_file)
			result, tot_samples = await self.recognize_stream_server(proc)
			await proc.wait()

			if tot_samples == 0:
				self.queue.task_done()
				continue

			processed_result: str = self.format_result(result)
			if output_file:
				output_path = Path(output_file)
				logger.info(f"File {output_path} processing complete")
				await asyncio.to_thread(output_path.write_text, processed_result, encoding="utf-8")

			elapsed: float = timer() - start_time
			logger.info(
				f"Execution time: {elapsed:.3f} sec; xRT {float(elapsed) * (2 * SAMPLE_RATE) / tot_samples:.3f}",
			)
			self.queue.task_done()

	def pool_worker(self, input_data: tuple[Path, Path]) -> None:
		"""
		A worker that processes a single transcription task from the pool.

		Args:
			input_data: A tuple containing the input and output file paths.

		"""
		input_file, output_file = input_data
		logger.info(f"Recognizing {input_file}")
		start_time: float = timer()

		try:
			stream: subprocess.Popen = self.resample_ffmpeg(input_file)
		except FileNotFoundError:
			logger.error("FFmpeg not found. Please install it and add it to your PATH.")
			return
		except Exception as e:
			logger.error(f"Error processing {input_file}: {e}")
			return

		rec: KaldiRecognizer = KaldiRecognizer(self.model, SAMPLE_RATE)
		rec.set_words(enable_words=True)
		result, tot_samples = self.recognize_stream(rec, stream)

		if tot_samples == 0:
			return

		processed_result: str = self.format_result(result)
		if output_file:
			output_path = Path(output_file)
			logger.info(f"File {output_path} processing complete")
			output_path.write_text(processed_result, encoding="utf-8")

		elapsed: float = timer() - start_time
		logger.info(f"Execution time: {elapsed:.3f} sec; xRT {float(elapsed) * (2 * SAMPLE_RATE) / tot_samples:.3f}")

	async def process_task_list_server(self, task_list: list[tuple[Path, Path | str]]) -> None:
		"""
		Processes a list of transcription tasks using a WebSocket server.

		Args:
			task_list: A list of tuples, each containing input and output file paths.

		"""
		for task in task_list:
			self.queue.put(task)
		workers = [asyncio.create_task(self.server_worker()) for _ in range(self.args.tasks)]
		await asyncio.gather(*workers)

	def process_task_list_pool(self, task_list: list[tuple[Path, Path | str]]) -> None:
		"""
		Processes a list of transcription tasks using a process pool.

		Args:
			task_list: A list of tuples, each containing input and output file paths.

		"""
		with Pool() as pool:
			pool.map(self.pool_worker, task_list)

	def process_task_list(self, task_list: list[tuple[Path, Path | str]]) -> None:
		"""
		Processes a list of transcription tasks either locally or using a server.

		Args:
			task_list: A list of tuples, each containing input and output file paths.

		"""
		if self.args.server is None:
			self.process_task_list_pool(task_list)
		else:
			asyncio.run(self.process_task_list_server(task_list))
