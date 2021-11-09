# coding=utf-8
import re
# [oov] no longer in words.txt
OOV_TERM = '<unk>'

def kaldi_normalize(word, model):
    '''Take a token extracted from a transcript by MetaSentence and
    transform it to use the same format as Kaldi's vocabulary files.
    Removes fancy punctuation and strips out-of-vocabulary words.
    Using vosk_model_find_word method to check is current word in vosk
    vocabulary?
    '''
    norm = word.lower()
    status = model.vosk_model_find_word(str(norm))
    # Turn fancy apostrophes into simpler apostrophes
    norm = norm.replace("’", "'")
    if len(norm) > 0 and status == -1:
        norm = OOV_TERM
    return norm

class MetaSentence:
    '''Maintain two parallel representations of a sentence: one for
    Kaldi's benefit, and the other in human-legible form.
    '''

    def __init__(self, sentence, model):
        self.raw_sentence = sentence
        self.model = model

        if type(sentence) == bytes:
            self.raw_sentence = sentence.decode('utf-8')

        self._tokenize()
           
    def _tokenize(self):
        self._seq = []
        for m in re.finditer(r'(\w|\’\w|\'\w)+', self.raw_sentence, re.UNICODE):
            start, end = m.span()
            word = m.group()
            token = kaldi_normalize(word, self.model)
            self._seq.append({
                "start": start, # as unicode codepoint offset
                "end": end, # as unicode codepoint offset
                "token": token,
            })

    def get_kaldi_sequence(self):
        return [x["token"] for x in self._seq]

    def get_display_sequence(self):
        display_sequence = []
        for x in self._seq:
            start, end = x["start"], x["end"]
            word = self.raw_sentence[start:end]
            display_sequence.append(word)
        return display_sequence

    def get_text_offsets(self):
        return [(x["start"], x["end"]) for x in self._seq]
