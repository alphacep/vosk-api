import pytest
import pathlib
from pathlib import Path
import vosk_align as aligner
'''Testing aligner script. You have to put your model in example folder for run'''

dir_path = pathlib.Path.cwd()

@pytest.fixture
def input_args1():
    input_wav = str(dir_path) + '/example/glorious.wav'
    input_txt = str(dir_path) + '/example/glorious.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_glory(input_args1):
    audiofile = input_args1[0]
    txtfile = input_args1[1]
    model = input_args1[2]
    output = ''
    aligner.main(audiofile, txtfile, model, output)
    
@pytest.fixture
def input_args2():
    input_wav = str(dir_path) + '/example/cats.wav'
    input_txt = str(dir_path) + '/example/cats.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_cats(input_args2):
    audiofile = input_args2[0]
    txtfile = input_args2[1]
    model = input_args2[2]
    output = ''
    aligner.main(audiofile, txtfile, model, output)

@pytest.fixture
def input_args3():
    input_wav = str(dir_path) + '/example/dagon.wav'
    input_txt = str(dir_path) + '/example/dagon.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_dagon(input_args3):
    audiofile = input_args3[0]
    txtfile = input_args3[1]
    model = input_args3[2]
    output = ''
    aligner.main(audiofile, txtfile, model, output)

@pytest.fixture
def input_args4():
    input_wav = str(dir_path) + '/example/polar.wav'
    input_txt = str(dir_path) + '/example/polar.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_polar(input_args4):
    audiofile = input_args4[0]
    txtfile = input_args4[1]
    model = input_args4[2]
    output = ''
    aligner.main(audiofile, txtfile, model, output)

@pytest.fixture
def input_args5():
    input_wav = str(dir_path) + '/example/wendy.wav'
    input_txt = str(dir_path) + '/example/wendy.txt'
    input_model = str(dir_path) + '/example/model'
    return input_wav, input_txt, input_model

def test_wendy(input_args5):
    audiofile = input_args5[0]
    txtfile = input_args5[1]
    model = input_args5[2]
    output = ''
    aligner.main(audiofile, txtfile, model, output)
