import logging
import re

from vosk import KaldiRecognizer
'''The script will rework.
    1.1 & 1.2 prepare input text
    2.1 get current sentence end-position as number
    3.1 divide sentences in text
    4.1 cut current sentence
    5.1 prepare text for KaldiRecognizer pattern
'''
def text_processor(text, model):

    # 3.1 
    def get_sentence(preprocess_result):
        symbols = re.findall(r'([^\.\?\!]{1})', preprocess_result)
        return symbols
    # 2.1
    def get_sentence_separator(preprocess_result):
        current_sentence = re.search(r'([\.\?\!]{1})', preprocess_result)
        current_separator_position = current_sentence.start()
        return current_separator_position
    # 5.1
    def prepared_part_for_KaldiRecognizer(make_sentence):
        final_result = ''.join(("", ''.join(('[', ''.join(('"', make_sentence.strip('[]'), '"')), ', "[unk]"]'))))
        return final_result
    # 1.1
    def preprocess(text):
        preprocessed_result = ''
        cleaning = re.sub(r'[\,\;]', '', text)
        lower_case = cleaning.lower()
        for symbol in lower_case:
            preprocessed_result += symbol
        return preprocessed_result
    # 4.1
    def raw_part(make_sentence, prepared_text):
        prepared_text  = ''.join(prepared_text.split(make_sentence))[1:]
        return prepared_text

    make_text = ''
    preprocessed_result = preprocess(text.strip()) # 1
    while(len(preprocessed_result) > 0):
        current_separator_position = get_sentence_separator(preprocessed_result)
        # 2
        symbols = get_sentence(preprocessed_result) # 3
        make_sentence = ''
        for symbol in range(current_separator_position):
            make_sentence += symbols[symbol]
        make_text += make_sentence
        preprocessed_result = raw_part(make_sentence, preprocessed_result) # 4
    final = prepared_part_for_KaldiRecognizer(make_text) # 5
    rec = KaldiRecognizer(model, 16000, final)
    return rec
