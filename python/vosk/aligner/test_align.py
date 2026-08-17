import pytest
import pathlib
import json
import argparse
import vosk_align as aligner

from pathlib import Path

'''Testing aligner script. You have to put your model in 'examples' folder for run'''
dir_path = pathlib.Path.cwd()

'''test_alltogether purpose: to check how aligner will align words if all cases below alltogether(missed_words, not_found_in_audio, not_found_in_transcript)'''
@pytest.fixture
def input_args_1():
    input_wav = str(dir_path) + '/examples/glorious.wav'
    input_txt = str(dir_path) + '/examples/glorious.txt'
    input_model = str(dir_path) + '/examples/model'
    return input_wav, input_txt, input_model

def test_alltogether(input_args_1):
    output=''
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'audiofile')
    parser.add_argument(
            'txtfile')
    parser.add_argument(
            'model')
    parser.add_argument(
            'output')
    args = parser.parse_args([input_args_1[0], input_args_1[1], input_args_1[2], output])
    result = aligner.get_result(args)
    with open('tests/glorious.log', 'r', encoding='utf-8') as glorious:
        glorious = glorious.read()
        new_result, new_glorious = json.loads(result), json.loads(glorious)
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
    input_wav = str(dir_path) + '/examples/cats.wav'
    input_txt = str(dir_path) + '/examples/cats.txt'
    input_model = str(dir_path) + '/examples/model'
    return input_wav, input_txt, input_model

def test_missed_words(input_args_2):
    output = ''
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'audiofile')
    parser.add_argument(
            'txtfile')
    parser.add_argument(
            'model')
    parser.add_argument(
            'output')
    args = parser.parse_args([input_args_2[0], input_args_2[1], input_args_2[2], output])
    result = aligner.get_result(args)
    with open('tests/cats.log', 'r', encoding='utf-8') as cats:
        cats = cats.read()
        new_result, new_cats = json.loads(result), json.loads(cats)
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
    input_wav = str(dir_path) + '/examples/dagon.wav'
    input_txt = str(dir_path) + '/examples/dagon.txt'
    input_model = str(dir_path) + '/examples/model'
    return input_wav, input_txt, input_model

def test_not_found_in_audio(input_args_3):
    output = ''
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'audiofile')
    parser.add_argument(
            'txtfile')
    parser.add_argument(
            'model')
    parser.add_argument(
            'output')
    args = parser.parse_args([input_args_3[0], input_args_3[1], input_args_3[2], output])
    result = aligner.get_result(args)
    with open('tests/dagon.log', 'r', encoding='utf-8') as dagon:
        dagon = dagon.read()
        new_result, new_dagon = json.loads(result), json.loads(dagon)
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
    input_wav = str(dir_path) + '/examples/polar.wav'
    input_txt = str(dir_path) + '/examples/polar.txt'
    input_model = str(dir_path) + '/examples/model'
    return input_wav, input_txt, input_model

def test_not_found_in_transcript(input_args_4):
    output = ''
    parser = argparse.ArgumentParser()
    parser.add_argument(
            'audiofile')
    parser.add_argument(
            'txtfile')
    parser.add_argument(
            'model')
    parser.add_argument(
            'output')
    args = parser.parse_args([input_args_4[0], input_args_4[1], input_args_4[2], output])
    result = aligner.get_result(args)
    with open('tests/polar.log', 'r', encoding='utf-8') as polar:
        polar = polar.read()
        new_result, new_polar = json.loads(result), json.loads(polar)
        match = True
        for i in range(len(new_result)):
            if new_result['words'][i] == new_polar['words'][i]:
                pass
            else:
                match = False
        assert match == True
