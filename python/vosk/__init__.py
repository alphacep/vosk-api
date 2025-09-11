import os
import sys
import srt
import datetime
import json
import enum

import requests
from urllib.request import urlretrieve
from zipfile import ZipFile
from re import match
from pathlib import Path
from .vosk_cffi import ffi as _ffi
from tqdm import tqdm

# Remote location of the models and local folders
MODEL_PRE_URL = "https://alphacephei.com/vosk/models/"
MODEL_LIST_URL = MODEL_PRE_URL + "model-list.json"
MODEL_DIRS = [os.getenv("VOSK_MODEL_PATH"), Path("/usr/share/vosk"),
        Path.home() / "AppData/Local/vosk", Path.home() / ".cache/vosk"]

def open_dll():
    dlldir = os.path.abspath(os.path.dirname(__file__))
    if sys.platform == "win32":
        # We want to load dependencies too
        os.environ["PATH"] = dlldir + os.pathsep + os.environ["PATH"]
        if hasattr(os, "add_dll_directory"):
            os.add_dll_directory(dlldir)
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.dll"))
    elif sys.platform == "linux":
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.so"))
    elif sys.platform == "darwin":
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.dyld"))
    else:
        raise TypeError("Unsupported platform")

_c = open_dll()

def list_models():
    response = requests.get(MODEL_LIST_URL, timeout=10)
    for model in response.json():
        print(model["name"])

def list_languages():
    response = requests.get(MODEL_LIST_URL, timeout=10)
    languages = {m["lang"] for m in response.json()}
    for lang in languages:
        print (lang)

class Model:
    def __init__(self, model_path=None, model_name=None, lang=None):
        if model_path is not None:
            self._handle = _c.vosk_model_new(model_path.encode("utf-8"))
        else:
            model_path = self.get_model_path(model_name, lang)
            self._handle = _c.vosk_model_new(model_path.encode("utf-8"))
        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a model")

    def __del__(self):
        if _c is not None:
            _c.vosk_model_free(self._handle)

    def vosk_model_find_word(self, word):
        return _c.vosk_model_find_word(self._handle, word.encode("utf-8"))

    def get_model_path(self, model_name, lang):
        if model_name is None:
            model_path = self.get_model_by_lang(lang)
        else:
            model_path = self.get_model_by_name(model_name)
        return str(model_path)

    def get_model_by_name(self, model_name):
        for directory in MODEL_DIRS:
            if directory is None or not Path(directory).exists():
                continue
            model_file_list = os.listdir(directory)
            model_file = [model for model in model_file_list if model == model_name]
            if model_file != []:
                return Path(directory, model_file[0])
        response = requests.get(MODEL_LIST_URL, timeout=10)
        result_model = [model["name"] for model in response.json() if model["name"] == model_name]
        if result_model == []:
            print("model name %s does not exist" % (model_name))
            sys.exit(1)
        else:
            self.download_model(Path(directory, result_model[0]))
            return Path(directory, result_model[0])

    def get_model_by_lang(self, lang):
        for directory in MODEL_DIRS:
            if directory is None or not Path(directory).exists():
                continue
            model_file_list = os.listdir(directory)
            model_file = [model for model in model_file_list if
                    match(r"vosk-model(-small)?-{}".format(lang), model)]
            if model_file != []:
                return Path(directory, model_file[0])
        response = requests.get(MODEL_LIST_URL, timeout=10)
        result_model = [model["name"] for model in response.json() if
                model["lang"] == lang and model["type"] == "small" and model["obsolete"] == "false"]
        if result_model == []:
            print("lang %s does not exist" % (lang))
            sys.exit(1)
        else:
            self.download_model(Path(directory, result_model[0]))
            return Path(directory, result_model[0])

    def download_model(self, model_name):
        if not (model_name.parent).exists():
            (model_name.parent).mkdir(parents=True)
        with tqdm(unit="B", unit_scale=True, unit_divisor=1024, miniters=1,
                desc=(MODEL_PRE_URL + str(model_name.name) + ".zip").rsplit("/",
                    maxsplit=1)[-1]) as t:
            reporthook = self.download_progress_hook(t)
            urlretrieve(MODEL_PRE_URL + str(model_name.name) + ".zip",
                    str(model_name) + ".zip", reporthook=reporthook, data=None)
            t.total = t.n
            with ZipFile(str(model_name) + ".zip", "r") as model_ref:
                model_ref.extractall(model_name.parent)
            Path(str(model_name) + ".zip").unlink()

    def download_progress_hook(self, t):
        last_b = [0]
        def update_to(b=1, bsize=1, tsize=None):
            if tsize not in (None, -1):
                t.total = tsize
            displayed = t.update((b - last_b[0]) * bsize)
            last_b[0] = b
            return displayed
        return update_to

class SpkModel:

    def __init__(self, model_path):
        self._handle = _c.vosk_spk_model_new(model_path.encode("utf-8"))

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a speaker model")

    def __del__(self):
        _c.vosk_spk_model_free(self._handle)

class EndpointerMode(enum.Enum):
    DEFAULT = 0
    SHORT = 1
    LONG = 2
    VERY_LONG = 3

class KaldiRecognizer:

    def __init__(self, *args):
        if len(args) == 2:
            self._handle = _c.vosk_recognizer_new(args[0]._handle, args[1])
        elif len(args) == 3 and isinstance(args[2], SpkModel):
            self._handle = _c.vosk_recognizer_new_spk(args[0]._handle,
                    args[1], args[2]._handle)
        elif len(args) == 3 and isinstance(args[2], str):
            self._handle = _c.vosk_recognizer_new_grm(args[0]._handle,
                    args[1], args[2].encode("utf-8"))
        else:
            raise TypeError("Unknown arguments")

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a recognizer")

    def __del__(self):
        _c.vosk_recognizer_free(self._handle)

    def SetMaxAlternatives(self, max_alternatives):
        _c.vosk_recognizer_set_max_alternatives(self._handle, max_alternatives)

    def SetWords(self, enable_words):
        _c.vosk_recognizer_set_words(self._handle, 1 if enable_words else 0)

    def SetResultOptions(self, options):
        _c.vosk_recognizer_set_result_options(self._handle, options.encode("utf-8"))

    def SetPartialWords(self, enable_partial_words):
        _c.vosk_recognizer_set_partial_words(self._handle, 1 if enable_partial_words else 0)

    def SetNLSML(self, enable_nlsml):
        _c.vosk_recognizer_set_nlsml(self._handle, 1 if enable_nlsml else 0)

    def SetEndpointerMode(self, mode):
        _c.vosk_recognizer_set_endpointer_mode(self._handle, mode.value)

    def SetEndpointerDelays(self, t_start_max, t_end, t_max):
        _c.vosk_recognizer_set_endpointer_delays(self._handle, t_start_max, t_end, t_max)

    def SetSpkModel(self, spk_model):
        _c.vosk_recognizer_set_spk_model(self._handle, spk_model._handle)

    def SetGrammar(self, grammar):
        _c.vosk_recognizer_set_grm(self._handle, grammar.encode("utf-8"))

    def AcceptWaveform(self, data):
        res = _c.vosk_recognizer_accept_waveform(self._handle, data, len(data))
        if res < 0:
            raise Exception("Failed to process waveform")
        return res

    def Result(self):
        return _ffi.string(_c.vosk_recognizer_result(self._handle)).decode("utf-8")

    def PartialResult(self):
        return _ffi.string(_c.vosk_recognizer_partial_result(self._handle)).decode("utf-8")

    def FinalResult(self):
        return _ffi.string(_c.vosk_recognizer_final_result(self._handle)).decode("utf-8")

    def Reset(self):
        return _c.vosk_recognizer_reset(self._handle)

    def SrtResult(self, stream, words_per_line = 7):
        results = []

        while True:
            data = stream.read(4000)
            if len(data) == 0:
                break
            if self.AcceptWaveform(data):
                results.append(self.Result())
        results.append(self.FinalResult())

        subs = []
        for res in results:
            jres = json.loads(res)
            if not "result" in jres:
                continue
            words = jres["result"]
            for j in range(0, len(words), words_per_line):
                line = words[j : j + words_per_line]
                s = srt.Subtitle(index=len(subs),
                        content=" ".join([l["word"] for l in line]),
                        start=datetime.timedelta(seconds=line[0]["start"]),
                        end=datetime.timedelta(seconds=line[-1]["end"]))
                subs.append(s)

        return srt.compose(subs)

def SetLogLevel(level):
    return _c.vosk_set_log_level(level)


def GpuInit():
    _c.vosk_gpu_init()


def GpuThreadInit():
    _c.vosk_gpu_thread_init()

class BatchModel:

    def __init__(self, model_path, *args):
        self._handle = _c.vosk_batch_model_new(model_path.encode('utf-8'))

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a model")

    def __del__(self):
        _c.vosk_batch_model_free(self._handle)

    def Wait(self):
        _c.vosk_batch_model_wait(self._handle)

class BatchRecognizer:

    def __init__(self, *args):
        self._handle = _c.vosk_batch_recognizer_new(args[0]._handle, args[1])

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a recognizer")

    def __del__(self):
        _c.vosk_batch_recognizer_free(self._handle)

    def AcceptWaveform(self, data):
        res = _c.vosk_batch_recognizer_accept_waveform(self._handle, data, len(data))

    def Result(self):
        ptr = _c.vosk_batch_recognizer_front_result(self._handle)
        res = _ffi.string(ptr).decode("utf-8")
        _c.vosk_batch_recognizer_pop(self._handle)
        return res

    def FinishStream(self):
        _c.vosk_batch_recognizer_finish_stream(self._handle)

    def GetPendingChunks(self):
        return _c.vosk_batch_recognizer_get_pending_chunks(self._handle)

class Processor:

    def __init__(self, *args):
        self._handle = _c.vosk_text_processor_new(args[0].encode('utf-8'), args[1].encode('utf-8'))

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create processor")

    def __del__(self):
        _c.vosk_text_processor_free(self._handle)

    def process(self, text):
        return _ffi.string(_c.vosk_text_processor_itn(self._handle, text.encode('utf-8'))).decode('utf-8')
