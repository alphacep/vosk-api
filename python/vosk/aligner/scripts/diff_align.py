import difflib
import numpy
import sys

from . import transcription
# TODO(maxhawkins): try using the (apparently-superior) time-mediated dynamic
# programming algorithm used in sclite's alignment process:
# http://www1.icsi.berkeley.edu/Speech/docs/sctk-1.2/sclite.htm#time-mediated
def align(alignment, ms):
    '''Use the diff algorithm to align the raw tokens recognized by Kaldi
    to the words in the transcript (tokenized by MetaSentence as ms).

    The output combines information about the timing and alignment of
    correctly-aligned words as well as words that Kaldi failed to recognize
    and extra words not found in the original transcript.
    '''
    conf = [X['conf'] for X in alignment]
    start = [X['start'] for X in alignment]
    end = [X['end'] for X in alignment]
    duration = list(numpy.around([end[X]-start[X] for X in range(len(end))], 2))
    hypothesis = [X['word'] for X in alignment]
    reference = ms.get_kaldi_sequence()
    display_seq = ms.get_display_sequence()
    txt_offsets = ms.get_text_offsets()
    out = []

    for op, a, b in word_diff(hypothesis, reference):
        try:
            display_word = display_seq[b] # index
        except IndexError:
            print('Please compare your txt and wav files, probably you have more words in txtfile than wavfile contain')
            exit (1)
        start_offset, end_offset = txt_offsets[b]
        if op == 'equal':
            hyp_word = hypothesis[a]
            hyp_token = alignment[a]
            out.append(transcription.Word(
                case=transcription.Word.SUCCESS,
                startOffset=start_offset,
                endOffset=end_offset,
                word=display_word,
                alignedWord=hyp_word,
                realign=False,
                conf=conf[a],
                start=start[a],
                end=end[a],
                duration=duration[a]))
        elif op == 'replace': # insert/delete ?
            if reference[b] == '<unk>':
                out.append(transcription.Word(
                    case=transcription.Word.NOT_FOUND_IN_TRANSCRIPT,
                    startOffset=start_offset,
                    endOffset=end_offset,
                    word=display_word,
                    realign=False))
            else:
                out.append(transcription.Word(
                    case=transcription.Word.NOT_FOUND_IN_AUDIO,
                    startOffset=start_offset,
                    endOffset=end_offset,
                    word=display_word,
                    realign=True))
    return out

def word_diff(a, b):
    '''Like difflib.SequenceMatcher but it only compares one word
    at a time. Returns an iterator whose elements are like
    (operation, index in a, index in b)
    '''
    matcher = difflib.SequenceMatcher(a=a, b=b)
    for op, a_idx, _, b_idx, _ in by_word(matcher.get_opcodes()):
        yield (op, a_idx, b_idx)

def by_word(opcodes):
    '''Take difflib.SequenceMatcher.get_opcodes() output and
    return an equivalent opcode sequence that only modifies
    one word at a time
    '''
    for op, s1, e1, s2, e2 in opcodes:
        if op == 'delete':
            for i in range(s1, e1):
                yield (op, i, i+1, s2, s2)
        elif op == 'insert':
            for i in range(s2, e2):
                yield (op, s1, s1, i, i+1)
        else:
            len1 = e1-s1
            len2 = e2-s2
            for i1, i2 in zip(range(s1, e1), range(s2, e2)):
                yield (op, i1, i1 + 1, i2, i2 + 1)
            if len1 > len2:
                for i in range(s1 + len2, e1):
                    yield ('delete', i, i+1, e2, e2)
            if len2 > len1:
                for i in range(s2 + len1, e2):
                    yield ('insert', s1, s1, i, i+1)
