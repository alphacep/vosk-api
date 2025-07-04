#!/usr/bin/env python3
"""
Provides a command-line interface for transcribing audio files using the Vosk library.

It supports transcribing individual files or entire directories, with options for specifying
the model, language, output format, and other parameters.
"""

import argparse
import logging
import sys
from pathlib import Path

from vosk_python import list_languages, list_models
from vosk_python.transcriber.transcriber import Transcriber

logger = logging.getLogger(__name__)

parser = argparse.ArgumentParser(description="Transcribe audio file and save result in selected format")
parser.add_argument("--model", "-m", type=str, help="Path to the Vosk model directory.")
parser.add_argument(
	"--server",
	"-s",
	type=str,
	help="Use a WebSocket server for recognition (e.g., ws://localhost:2700).",
)
parser.add_argument("--list-models", default=False, action="store_true", help="List available models and exit.")
parser.add_argument("--list-languages", default=False, action="store_true", help="List available languages and exit.")
parser.add_argument("--model-name", "-n", type=str, help="Select a model by its name.")
parser.add_argument("--lang", "-l", default="en-us", type=str, help="Select a model by language (e.g., 'en-us').")
parser.add_argument("--input", "-i", type=str, help="Path to an audio file or a directory of audio files.")
parser.add_argument("--output", "-o", default="", type=str, help="Optional path to the output file or directory.")
parser.add_argument(
	"--output-type",
	"-t",
	default="txt",
	type=str,
	help="Output data type (e.g., 'txt', 'srt', 'json').",
)
parser.add_argument("--tasks", "-ts", default=10, type=int, help="Number of parallel recognition tasks.")
parser.add_argument("--log-level", default="INFO", help="Set the logging level (e.g., 'DEBUG', 'INFO', 'WARNING').")


def main() -> None:
	"""
	Parses command-line arguments and initiates the transcription process.
	"""
	args = parser.parse_args()
	log_level: str = args.log_level.upper()
	logger.setLevel(log_level)

	if args.list_models:
		list_models()
		return

	if args.list_languages:
		list_languages()
		return

	if not args.input:
		logger.info("Please specify an input file or directory.")
		sys.exit(1)

	input_path = Path(args.input)
	if not input_path.exists():
		logger.info(f"File or folder '{args.input}' does not exist. Please specify an existing file or directory.")
		sys.exit(1)

	transcriber = Transcriber(args)

	task_list: list[tuple[Path, Path | str]] = []
	if input_path.is_dir():
		output_dir = Path(args.output)
		task_list = [
			(input_path / fn, output_dir / f"{fn.stem}.{args.output_type}")
			for fn in input_path.iterdir()
			if fn.is_file()
		]
	elif input_path.is_file():
		output_path = Path(args.output) if args.output else ""
		task_list = [(input_path, output_path)]
	else:
		logger.info("Invalid input path. Please provide a valid file or directory.")
		sys.exit(1)

	transcriber.process_task_list(task_list)


if __name__ == "__main__":
	main()
