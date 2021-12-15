import pytest
import pathlib
from pathlib import Path
import vosk_align as aligner
import json
'''Testing aligner script. You have to put your model in example folder for run'''

dir_path = pathlib.Path.cwd()

def json_parser(result, log):
    parse_result = json.loads(result)
    parse_log = json.loads(log)
    return parse_result, parse_log

'''test_alltogether purpose: to check how aligner will align words if all cases below alltogether(missed_words, not_found_in_audio, not_found_in_transcript)'''
@pytest.fixture
def input_args_1():
    input_wav = str(dir_path) + '/example/glorious.wav'
    input_txt = str(dir_path) + '/example/glorious.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_alltogether(input_args_1):
    audiofile = input_args_1[0]
    txtfile = input_args_1[1]
    model = input_args_1[2]
    output = ''
    result = aligner.main(audiofile, txtfile, model, output)
    with open('glorious.log', 'r', encoding='utf-8') as glorious:
        glorious = glorious.read()
        new_result, new_glorious = json_parser(result, glorious)
        match = True
        for i in range(len(new_result)):
            if new_result['words'][i] == new_glorious['words'][i]:
                pass
            else:
                match = False
        assert match == True 

'''test_missed_words purpose: to check how aligner will align words if there are missed words in textfile. From one to four words was deleted in random places of the txtfile.
'''
@pytest.fixture
def input_args_2():
    input_wav = str(dir_path) + '/example/cats.wav'
    input_txt = str(dir_path) + '/example/cats.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_missed_words(input_args_2):
    audiofile = input_args_2[0]
    txtfile = input_args_2[1]
    model = input_args_2[2]
    output = ''
    result = aligner.main(audiofile, txtfile, model, output)
    with open('cats.log', 'r', encoding='utf-8') as cats:
        cats = cats.read()
        new_result, new_cats = json_parser(result, cats)
        match = True
        for i in range(len(new_result)):
            if new_result['words'][i] == new_cats['words'][i]:
                pass
            else:
                match = False
        assert match == True

'''test_not_found_in_audio purpose: to check how aligner will align words if there are some words in random places with case not_found_in_audio, but still in vocabulary.
'''
@pytest.fixture
def input_args_3():
    input_wav = str(dir_path) + '/example/dagon.wav'
    input_txt = str(dir_path) + '/example/dagon.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_not_found_in_audio(input_args_3):
    audiofile = input_args_3[0]
    txtfile = input_args_3[1]
    model = input_args_3[2]
    output = ''
    result = aligner.main(audiofile, txtfile, model, output)
    with open('dagon.log', 'r', encoding='utf-8') as dagon:
        dagon = dagon.read()
        new_result, new_dagon = json_parser(result, dagon)
        match = True
        for i in range(len(new_result)):
            if new_result['words'][i] == new_dagon['words'][i]:
                pass
            else:
                match = False
        assert match == True

'''test_not_found_in_transcript purpose: to check how aligner will align words if there are some words in random places with case not_found_in_transcript.
'''
@pytest.fixture
def input_args_4():
    input_wav = str(dir_path) + '/example/polar.wav'
    input_txt = str(dir_path) + '/example/polar.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_not_found_in_transcript(input_args_4):
    audiofile = input_args_4[0]
    txtfile = input_args_4[1]
    model = input_args_4[2]
    output = ''
    result = aligner.main(audiofile, txtfile, model, output)
    with open('polar.log', 'r', encoding='utf-8') as polar:
        polar = polar.read()
        new_result, new_polar = json_parser(result, polar)
        match = True
        for i in range(len(new_result)):
            if new_result['words'][i] == new_polar['words'][i]:
                pass
            else:
                match = False
        assert match == True
