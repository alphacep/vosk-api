import datetime
import enum
import json
import os
import sys
from collections.abc import Callable, Iterator
from pathlib import Path
from re import match
from typing import Any
from zipfile import ZipFile

import requests
import srt
from rich import print as rprint
from tqdm import tqdm

from .vosk_cffi import ffi as _ffi  # type: ignore

# Remote location of the models and local folders
MODEL_PRE_URL: str = "https://alphacephei.com/vosk/models/"
MODEL_LIST_URL: str = MODEL_PRE_URL + "model-list.json"
MODEL_DIRS: list[Path] = [
	Path(os.environ.get("VOSK_MODEL_PATH", "")) if os.environ.get("VOSK_MODEL_PATH") else Path(),
	Path("/usr/share/vosk"),
	Path.home() / "AppData/Local/vosk_python",
	Path.home() / ".cache/vosk_python",
]


def open_dll() -> Any:
	"""
	Loads the Vosk dynamic library based on the operating system.

	Returns:
		The CFFI library object for the loaded Vosk library.

	Raises:
		TypeError: If the platform is not supported.

	"""
	dlldir = Path(__file__).parent.resolve()
	if sys.platform == "win32":
		os.environ["PATH"] = str(dlldir) + os.pathsep + os.environ["PATH"]
		if hasattr(os, "add_dll_directory"):
			os.add_dll_directory(str(dlldir))
		return _ffi.dlopen(str(dlldir / "libvosk.dll"))
	if sys.platform == "linux":
		return _ffi.dlopen(str(dlldir / "libvosk.so"))
	if sys.platform == "darwin":
		return _ffi.dlopen(str(dlldir / "libvosk.dyld"))
	raise TypeError("Unsupported platform")


_c: Any = open_dll()


def list_models() -> None:
	"""
	Fetches and prints a list of available Vosk models.
	"""
	response = requests.get(MODEL_LIST_URL, timeout=10)
	for model in response.json():
		rprint(model)


def list_languages() -> None:
	"""
	Fetches and prints a list of supported languages.
	"""
	response = requests.get(MODEL_LIST_URL, timeout=10)
	languages: set[str] = {m["lang"] for m in response.json()}
	for lang in languages:
		rprint(lang)


class Model:
	"""
	A class to manage a Vosk speech recognition model.

	This class handles the loading of a model from a local path or downloading it if not found.
	"""

	def __init__(
		self,
		model_path: str | None = None,
		model_name: str | None = None,
		lang: str = "en_us",
	) -> None:
		"""
		Initializes a Vosk model.

		Args:
			model_path: The path to the model directory.
			model_name: The name of the model to use.
			lang: The language of the model to use.

		Raises:
			Exception: If the model fails to be created.

		"""
		if model_path:
			self._handle = _c.vosk_model_new(str(model_path).encode("utf-8"))
		else:
			model_path = self._get_model_path(model_name, lang).__str__()
			self._handle = _c.vosk_model_new(str(model_path).encode("utf-8"))

		if self._handle == _ffi.NULL:
			raise Exception("Failed to create a model")

	def __del__(self) -> None:
		"""
		Frees the model resources when the object is destroyed.
		"""
		if _c is not None:
			_c.vosk_model_free(self._handle)

	def vosk_model_find_word(self, word: str) -> int:
		"""
		Finds a word in the model's dictionary.

		Args:
			word: The word to find.

		Returns:
			The word ID if found, otherwise -1.

		"""
		return _c.vosk_model_find_word(self._handle, word.encode("utf-8"))

	def _get_model_path(self, model_name: str | None, lang: str = "en_us") -> Path:
		"""
		Gets the path to a model, downloading it if necessary.

		Args:
			model_name: The name of the model.
			lang: The language of the model.

		Returns:
			The path to the model directory.

		"""
		model_path = self._get_model_by_lang(lang) if model_name is None else self._get_model_by_name(model_name)
		return model_path

	def _get_model_by_name(self, model_name: str) -> Path:
		"""
		Finds a model by name, downloading it if necessary.

		Args:
			model_name: The name of the model to find.

		Returns:
			The path to the model directory.

		"""
		for directory in MODEL_DIRS:
			if directory.exists():
				for model_file in directory.iterdir():
					if model_file.name == model_name:
						return model_file

		response = requests.get(MODEL_LIST_URL, timeout=10)
		result_model = [model["name"] for model in response.json() if model["name"] == model_name]
		if not result_model:
			sys.exit(1)

		self._download_model(directory / result_model[0])
		return directory / result_model[0]

	def _get_model_by_lang(self, lang: str) -> Path:
		"""
		Finds a model by language, downloading it if necessary.

		Args:
			lang: The language of the model to find.

		Returns:
			The path to the model directory.

		"""
		for directory in MODEL_DIRS:
			if directory.exists():
				for model_file in directory.iterdir():
					if match(rf"vosk-model(-small)?-{lang}", model_file.name):
						return model_file

		response = requests.get(MODEL_LIST_URL, timeout=10)
		result_model = [
			model["name"]
			for model in response.json()
			if model["lang"] == lang and model["type"] == "small" and not model["obsolete"]
		]
		if not result_model:
			sys.exit(1)

		self._download_model(directory / result_model[0])
		return directory / result_model[0]

	def _download_model(self, model_name: Path) -> None:
		"""
		Downloads a model from the remote server.

		Args:
			model_name: The name of the model to download.

		"""
		if not model_name.parent.exists():
			model_name.parent.mkdir(parents=True)

		with tqdm(
			unit="B",
			unit_scale=True,
			unit_divisor=1024,
			miniters=1,
			desc=(MODEL_PRE_URL + model_name.name + ".zip").rsplit("/", maxsplit=1)[-1],
		) as t:
			response = requests.get(MODEL_PRE_URL + model_name.name + ".zip", stream=True, timeout=10)
			with (model_name.parent / (model_name.name + ".zip")).open("wb") as f:
				for chunk in response.iter_content(chunk_size=1024):
					if chunk:
						f.write(chunk)
						t.update(len(chunk))

			with ZipFile(str(model_name) + ".zip", "r") as model_ref:
				model_ref.extractall(model_name.parent)

			(model_name.parent / (model_name.name + ".zip")).unlink()

	def _download_progress_hook(self, t: tqdm) -> Callable[[int, int, int | None], Any]:
		"""
		Creates a progress hook for the model download.

		Args:
			t: The tqdm progress bar instance.

		Returns:
			A function that updates the progress bar.

		"""
		last_b = [0]

		def update_to(b: int = 1, bsize: int = 1, tsize: int | None = None) -> None:
			if tsize is not None:
				t.total = tsize
			t.update((b - last_b[0]) * bsize)
			last_b[0] = b

		return update_to


class SpkModel:
	"""
	A class to manage a Vosk speaker identification model.
	"""

	def __init__(self, model_path: str) -> None:
		"""
		Initializes a speaker model.

		Args:
			model_path: The path to the speaker model directory.

		Raises:
			Exception: If the speaker model fails to be created.

		"""
		self._handle = _c.vosk_spk_model_new(model_path.encode("utf-8"))
		if self._handle == _ffi.NULL:
			raise Exception("Failed to create a speaker model")

	def __del__(self) -> None:
		"""
		Frees the speaker model resources when the object is destroyed.
		"""
		_c.vosk_spk_model_free(self._handle)


class EndpointerMode(enum.Enum):
	"""
	An enumeration for the endpointer mode.
	"""

	DEFAULT = 0
	SHORT = 1
	LONG = 2
	VERY_LONG = 3


class KaldiRecognizer:
	"""
	A class to perform speech recognition using a Kaldi model.
	"""

	def __init__(self, *args: Any) -> None:
		"""
		Initializes a Kaldi recognizer.

		Args:
			*args: Variable length argument list.
				Can be (Model, float) for a simple recognizer,
				(Model, float, SpkModel) for a speaker-aware recognizer, or
				(Model, float, str) for a grammar-based recognizer.

		Raises:
			TypeError: If the arguments are of an unknown type.
			Exception: If the recognizer fails to be created.

		"""
		if len(args) == 2:
			self._handle = _c.vosk_recognizer_new(args[0]._handle, args[1])
		elif len(args) == 3 and isinstance(args[2], SpkModel):
			self._handle = _c.vosk_recognizer_new_spk(args[0]._handle, args[1], args[2]._handle)
		elif len(args) == 3 and isinstance(args[2], str):
			self._handle = _c.vosk_recognizer_new_grm(args[0]._handle, args[1], args[2].encode("utf-8"))
		else:
			raise TypeError("Unknown arguments")

		if self._handle == _ffi.NULL:
			raise Exception("Failed to create a recognizer")

	def __del__(self) -> None:
		"""
		Frees the recognizer resources when the object is destroyed.
		"""
		_c.vosk_recognizer_free(self._handle)

	def set_max_alternatives(self, max_alternatives: int) -> None:
		"""
		Sets the maximum number of alternative recognition results.

		Args:
			max_alternatives: The maximum number of alternatives.

		"""
		_c.vosk_recognizer_set_max_alternatives(self._handle, max_alternatives)

	def set_words(self, enable_words: bool) -> None:
		"""
		Enables or disables word-level details in the recognition result.

		Args:
			enable_words: True to enable word-level details, False to disable.

		"""
		_c.vosk_recognizer_set_words(self._handle, 1 if enable_words else 0)

	def set_partial_words(self, enable_partial_words: bool) -> None:
		"""
		Enables or disables partial word-level details in the recognition result.

		Args:
			enable_partial_words: True to enable partial word-level details, False to disable.

		"""
		_c.vosk_recognizer_set_partial_words(self._handle, 1 if enable_partial_words else 0)

	def set_nlsml(self, enable_nlsml: bool) -> None:
		"""
		Enables or disables NLSML format in the recognition result.

		Args:
			enable_nlsml: True to enable NLSML format, False to disable.

		"""
		_c.vosk_recognizer_set_nlsml(self._handle, 1 if enable_nlsml else 0)

	def set_endpointer_mode(self, mode: EndpointerMode) -> None:
		"""
		Sets the endpointer mode.

		Args:
			mode: The endpointer mode to set.

		"""
		_c.vosk_recognizer_set_endpointer_mode(self._handle, mode.value)

	def set_endpointer_delays(self, t_start_max: float, t_end: float, t_max: float) -> None:
		"""
		Sets the endpointer delays.

		Args:
			t_start_max: Maximum delay for the start of speech.
			t_end: Delay for the end of speech.
			t_max: Maximum duration of speech.

		"""
		_c.vosk_recognizer_set_endpointer_delays(self._handle, t_start_max, t_end, t_max)

	def set_spk_model(self, spk_model: SpkModel) -> None:
		"""
		Sets the speaker model for the recognizer.

		Args:
			spk_model: The speaker model to set.

		"""
		_c.vosk_recognizer_set_spk_model(self._handle, spk_model._handle)

	def set_grammar(self, grammar: str) -> None:
		"""
		Sets the grammar for the recognizer.

		Args:
			grammar: The grammar to set.

		"""
		_c.vosk_recognizer_set_grm(self._handle, grammar.encode("utf-8"))

	def accept_waveform(self, data: bytes) -> int:
		"""
		Accepts a waveform for recognition.

		Args:
			data: The audio data to process.

		Returns:
			1 if a final result is available, 0 otherwise.

		Raises:
			Exception: If the waveform fails to be processed.

		"""
		res = _c.vosk_recognizer_accept_waveform(self._handle, data, len(data))
		if res < 0:
			raise Exception("Failed to process waveform")
		return res

	def result(self) -> str:
		"""
		Returns the current recognition result.

		Returns:
			The recognition result as a JSON string.

		"""
		return _ffi.string(_c.vosk_recognizer_result(self._handle)).decode("utf-8")

	def partial_result(self) -> str:
		"""
		Returns the partial recognition result.

		Returns:
			The partial recognition result as a JSON string.

		"""
		return _ffi.string(_c.vosk_recognizer_partial_result(self._handle)).decode("utf-8")

	def final_result(self) -> str:
		"""
		Returns the final recognition result.

		Returns:
			The final recognition result as a JSON string.

		"""
		return _ffi.string(_c.vosk_recognizer_final_result(self._handle)).decode("utf-8")

	def reset(self) -> int:
		"""
		Resets the recognizer.

		Returns:
			0 on success.

		"""
		return _c.vosk_recognizer_reset(self._handle)

	def srt_result(self, stream: Iterator[bytes], words_per_line: int = 7) -> str:
		"""
		Generates an SRT formatted result from an audio stream.

		Args:
			stream: An iterator that yields audio data chunks.
			words_per_line: The number of words per line in the SRT file.

		Returns:
			The SRT formatted result as a string.

		"""
		results: list[str] = []

		for data in stream:
			if self.accept_waveform(data):
				results.append(self.result())
		results.append(self.final_result())

		subs: list[srt.Subtitle] = []
		for res in results:
			jres = json.loads(res)
			if "result" not in jres:
				continue
			words = jres["result"]
			for j in range(0, len(words), words_per_line):
				line = words[j : j + words_per_line]
				s = srt.Subtitle(
					index=len(subs),
					content=" ".join([word["word"] for word in line]),
					start=datetime.timedelta(seconds=line[0]["start"]),
					end=datetime.timedelta(seconds=line[-1]["end"]),
				)
				subs.append(s)

		return srt.compose(subs)


def set_log_level(level: int) -> int:
	"""
	Sets the log level for the Vosk library.

	Args:
		level: The log level to set.

	Returns:
		The previous log level.

	"""
	return _c.vosk_set_log_level(level)


def gpu_init() -> None:
	"""
	Initializes the GPU for recognition.
	"""
	_c.vosk_gpu_init()


def gpu_thread_init() -> None:
	"""
	Initializes the GPU for the current thread.
	"""
	_c.vosk_gpu_thread_init()


class BatchModel:
	"""
	A class to manage a batch of recognition models for parallel processing.
	"""

	def __init__(self, model_path: str, *args: Any) -> None:
		"""
		Initializes a batch model.

		Args:
			model_path: The path to the model directory.
			*args: Additional arguments.

		Raises:
			Exception: If the batch model fails to be created.

		"""
		self._handle = _c.vosk_batch_model_new(model_path.encode("utf-8"))
		if self._handle == _ffi.NULL:
			raise Exception("Failed to create a batch model")

	def __del__(self) -> None:
		"""
		Frees the batch model resources when the object is destroyed.
		"""
		_c.vosk_batch_model_free(self._handle)

	def wait(self) -> None:
		"""
		Waits for the batch processing to complete.
		"""
		_c.vosk_batch_model_wait(self._handle)


class BatchRecognizer:
	"""
	A class to perform batch recognition.
	"""

	def __init__(self, *args: Any) -> None:
		"""
		Initializes a batch recognizer.

		Args:
			*args: Variable length argument list.

		Raises:
			Exception: If the batch recognizer fails to be created.

		"""
		self._handle = _c.vosk_batch_recognizer_new(args[0]._handle, args[1])
		if self._handle == _ffi.NULL:
			raise Exception("Failed to create a batch recognizer")

	def __del__(self) -> None:
		"""
		Frees the batch recognizer resources when the object is destroyed.
		"""
		_c.vosk_batch_recognizer_free(self._handle)

	def accept_waveform(self, data: bytes) -> None:
		"""
		Accepts a waveform for batch recognition.

		Args:
			data: The audio data to process.

		"""
		_c.vosk_batch_recognizer_accept_waveform(self._handle, data, len(data))

	def result(self) -> str:
		"""
		Returns the result of the batch recognition.

		Returns:
			The recognition result as a JSON string.

		"""
		ptr = _c.vosk_batch_recognizer_front_result(self._handle)
		res = _ffi.string(ptr).decode("utf-8")
		_c.vosk_batch_recognizer_pop(self._handle)
		return res

	def finish_stream(self) -> None:
		"""
		Finishes the processing of the current stream.
		"""
		_c.vosk_batch_recognizer_finish_stream(self._handle)

	def get_pending_chunks(self) -> int:
		"""
		Gets the number of pending chunks in the batch recognizer.

		Returns:
			The number of pending chunks.

		"""
		return _c.vosk_batch_recognizer_get_pending_chunks(self._handle)


class Processor:
	"""
	A class for text processing, such as inverse text normalization (ITN).
	"""

	def __init__(self, *args: Any) -> None:
		"""
		Initializes a text processor.

		Args:
			*args: Variable length argument list.

		Raises:
			Exception: If the processor fails to be created.

		"""
		self._handle = _c.vosk_text_processor_new(args[0].encode("utf-8"), args[1].encode("utf-8"))
		if self._handle == _ffi.NULL:
			raise Exception("Failed to create processor")

	def __del__(self) -> None:
		"""
		Frees the processor resources when the object is destroyed.
		"""
		_c.vosk_text_processor_free(self._handle)

	def process(self, text: str) -> str:
		"""
		Processes a text string.

		Args:
			text: The text to process.

		Returns:
			The processed text.

		"""
		return _ffi.string(_c.vosk_text_processor_itn(self._handle, text.encode("utf-8"))).decode("utf-8")
