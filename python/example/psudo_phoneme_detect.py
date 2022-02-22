#!/usr/bin/env python3

from vosk import Model, KaldiRecognizer
import wave
import json

# SetLogLevel(0)

wf = wave.open("test.wav", "rb")
sample_rate = 16000
model = Model("vosk-model-small-en-us-0.15")
rec = KaldiRecognizer(model, sample_rate)

file = open("output.txt", "w+")

# master_list = np.array([])
master_list = []


def list_creation():
    # master_list.fill(json.loads(rec.Result())['result'])
    master_list.extend(json.loads(rec.Result())['result'])


while True:
    data = wf.readframes(4096)
    rec.SetWords(True)
    if len(data) == 0:
        break
    if rec.AcceptWaveform(data):
        list_creation()
        # print(rec.Result())

# we need to run this separately after while loop to add last list to master list
list_creation()

word_duretion_array = []
word_count_array = []
word_start_array = []
# word_end_array = []
word_array = []
phonem_tightness_thrush_hold = 0.010

def list_processes():
    for key in master_list:
        # print(key)  # {'conf': 0.902826, 'end': 0.39, 'start': 0.21, 'word': 'i'}
        # making duretion array
        word_duretion = "{:.3f}".format(key["end"] - (key["start"] - phonem_tightness_thrush_hold))
        word_duretion_array.append(word_duretion)
        # print(word_duretion_array)
        # making word_count_array
        word_count_array.append(len(key['word']))
        # print(word_count_array)
        word_array.append(key['word'])
        # print(word_array)
        # making word_start_array
        word_start_array.append("{:.3f}".format(key['start']))
        # print(word_start_array)
        # word_end_array.append("{:.3f}".format(key['end']))
        # print(word_end_array)
        # print('\n')


list_processes()

for_loop_round = len(word_count_array)
phonem_duretion_array = []

def each_phonem_duretion_per_word():
    for key in range(0, for_loop_round):
        duretion = word_duretion_array[key]
        tag_time = word_count_array[key]
        phonem_duretion = float(duretion) / float(tag_time)
        phonem_duretion_array.append("{:.3f}".format(phonem_duretion))
        print(phonem_duretion_array)
each_phonem_duretion_per_word()

each_phonem_start_tag = []
def psudo_each_phonem_start_tag():
    for key in range(0, for_loop_round):
        duretion = float(phonem_duretion_array[key])
        start_tag = float(word_start_array[key])
        tag_time = word_count_array[key]
        sub_list = []
        # sub_list = {}
        # print(tag_time)
        if tag_time == 1:
            sub_list.append({"{:.3f}".format(start_tag): word_array[key]})
            each_phonem_start_tag.extend(sub_list)
        elif tag_time > 1:
            for j in range(0, tag_time):
                if j == 0:
                    # sub_list.append("{:.3f}".format(start_tag))
                    sub_list.append({"{:.3f}".format(start_tag): word_array[key][j]})
                else:
                    start_tag += duretion
                    # sub_list.append("{:.3f}".format(start_tag))
                    sub_list.append({"{:.3f}".format(start_tag): word_array[key][j]})
            each_phonem_start_tag.extend(sub_list)
psudo_each_phonem_start_tag()

#final result ... 
print(each_phonem_start_tag)
