import os
import sys
import requests
import urllib.request
import zipfile
import re

from pathlib import Path
from .vosk_cffi import ffi as _ffi

MODEL_PRE_PATH = 'https://alphacephei.com/vosk/models/'
MODEL_LIST_URL = MODEL_PRE_PATH + 'model-list.json'

def open_dll():
    dlldir = os.path.abspath(os.path.dirname(__file__))
    if sys.platform == 'win32':
        # We want to load dependencies too
        os.environ["PATH"] = dlldir + os.pathsep + os.environ['PATH']
        if hasattr(os, 'add_dll_directory'):
            os.add_dll_directory(dlldir)
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.dll"))
    elif sys.platform == 'linux':
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.so"))
    elif sys.platform == 'darwin':
        return _ffi.dlopen(os.path.join(dlldir, "libvosk.dyld"))
    else:
        raise TypeError("Unsupported platform")

_c = open_dll()

class Model(object):
    def __init__(self, model_path=None, model_name=None, lang=None):
        if model_path != None and model_name == None and lang == None:
            self._handle = _c.vosk_model_new(model_path.encode('utf-8'))
        else:
            model_path = self.get_model(model_name, lang)
            self._handle = _c.vosk_model_new(model_path.encode('utf-8'))
        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a model")

    def __del__(self):
        _c.vosk_model_free(self._handle)

    def vosk_model_find_word(self, word):
        return _c.vosk_model_find_word(self._handle, word.encode('utf-8'))
    
    def get_model_by_name(self, model_name, models_path):
        if not Path(models_path, model_name).is_dir():
            response = requests.get(MODEL_LIST_URL)
            result = [model['name'] for model in response.json() if model['name'] == model_name]
            if result == []:
                raise Exception("model name %s does not exist" % (model_name))
            else:
                result = result[0]
        else:
            result = model_name
        return result

    def get_model_by_lang(self, lang, models_path):
        model_file_list = os.listdir(models_path)
        model_file = [model for model in model_file_list if re.match(f"vosk-model(-small)?-{lang}", model)]
        if model_file == []:
            response = requests.get(MODEL_LIST_URL)
            result = [model['name'] for model in response.json() if model['lang'] == lang and model['type'] == 'small' and model['obsolete'] == 'false']
            if result == []:
                raise Exception("lang %s does not exist" % (lang))
            else:
                result = result[0]
        else:
            result = model_file[0]
        return result

    def get_model(self, model_name=None, lang=None):
        models_path = Path.home() / '.cache' / 'vosk'
        if not models_path.is_dir():
            models_path.mkdir()
        if lang == None:
            result = self.get_model_by_name(model_name, models_path)
        else:
            result = self.get_model_by_lang(lang, models_path)
        model_location = Path(models_path, result)
        if not model_location.exists():
            model_zip = str(model_location) + '.zip'
            urllib.request.urlretrieve(MODEL_PRE_PATH + str(model_location.name) + '.zip', model_zip)
            with zipfile.ZipFile(model_zip, 'r') as model_ref:
                model_ref.extractall(models_path)
            Path.unlink(Path(model_zip))
        return str(model_location)

class SpkModel(object):

    def __init__(self, model_path):
        self._handle = _c.vosk_spk_model_new(model_path.encode('utf-8'))

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a speaker model")

    def __del__(self):
        _c.vosk_spk_model_free(self._handle)

class KaldiRecognizer(object):

    def __init__(self, *args):
        if len(args) == 2:
            self._handle = _c.vosk_recognizer_new(args[0]._handle, args[1])
        elif len(args) == 3 and type(args[2]) is SpkModel:
            self._handle = _c.vosk_recognizer_new_spk(args[0]._handle, args[1], args[2]._handle)
        elif len(args) == 3 and type(args[2]) is str:
            self._handle = _c.vosk_recognizer_new_grm(args[0]._handle, args[1], args[2].encode('utf-8'))
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

    def SetPartialWords(self, enable_partial_words):
        _c.vosk_recognizer_set_partial_words(self._handle, 1 if enable_partial_words else 0)

    def SetNLSML(self, enable_nlsml):
        _c.vosk_recognizer_set_nlsml(self._handle, 1 if enable_nlsml else 0)

    def SetSpkModel(self, spk_model):
        _c.vosk_recognizer_set_spk_model(self._handle, spk_model._handle)

    def AcceptWaveform(self, data):
        res = _c.vosk_recognizer_accept_waveform(self._handle, data, len(data))
        if res < 0:
            raise Exception("Failed to process waveform")
        return res

    def Result(self):
        return _ffi.string(_c.vosk_recognizer_result(self._handle)).decode('utf-8')

    def PartialResult(self):
        return _ffi.string(_c.vosk_recognizer_partial_result(self._handle)).decode('utf-8')

    def FinalResult(self):
        return _ffi.string(_c.vosk_recognizer_final_result(self._handle)).decode('utf-8')

    def Reset(self):
        return _c.vosk_recognizer_reset(self._handle)


def SetLogLevel(level):
    return _c.vosk_set_log_level(level)


def GpuInit():
    _c.vosk_gpu_init()


def GpuThreadInit():
    _c.vosk_gpu_thread_init()

class BatchModel(object):

    def __init__(self, *args):
        self._handle = _c.vosk_batch_model_new()

        if self._handle == _ffi.NULL:
            raise Exception("Failed to create a model")

    def __del__(self):
        _c.vosk_batch_model_free(self._handle)

    def Wait(self):
        _c.vosk_batch_model_wait(self._handle)

class BatchRecognizer(object):

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
        res = _ffi.string(ptr).decode('utf-8')
        _c.vosk_batch_recognizer_pop(self._handle)
        return res

    def FinishStream(self):
        _c.vosk_batch_recognizer_finish_stream(self._handle)

    def GetPendingChunks(self):
        return _c.vosk_batch_recognizer_get_pending_chunks(self._handle)
