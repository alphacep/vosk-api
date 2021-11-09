import logging
import wave
import sys

from . import metasentence
from . import language_model
from . import diff_align
from . import transcription
from .transcriber import Transcriber as transcriber
'''The script will rework.
Multipass realign unaligned words.
Prepare multipass checking words sequence, when word's case ==
not-found-in-audio preparing chunk to realign like [words before, unaligned
words, words after], creating new personam small language and acoustic models
for the chunk, putting back into result sequence.
'''
def prepare_multipass(alignment):
    to_realign = []
    chunks = 0
    for i, w in enumerate(alignment):
        if w.case == 'not-found-in-audio':
            for j, wd in enumerate(alignment):
                if j >= max(0, i-3) and j <= min(len(alignment), i+3):
                    wd.realign = True
    cur_list = []
    start_idx = []
    end_idx = []
    start_counter = 0
    end_counter = 0
    for j, wd in enumerate(alignment):
        if j == 0 and (wd.case == 'not-found-in-audio' or wd.case == 'not-found-in-transcript'):
            start_idx.append(0)
        elif j == len(alignment)-1 and (wd.case == 'not-found-in-audio' or wd.case == 'not-found-in-transcript'):       
            end_idx.append(len(alignment)-1)

        if wd.realign:
            cur_list.append(wd)

            if chunks == start_counter:
                start_idx.append(j)
                start_counter += 1
        else:

            if len(cur_list) != 0:
                to_realign.append(cur_list)
                cur_list = []
                chunks += 1

            if chunks == end_counter+1:
                end_idx.append(j-1)
                end_counter += 1

    if len(cur_list) != 0:
        to_realign.append(cur_list)
        chunks += 1

    return to_realign, chunks, start_idx, end_idx

def realign(alignment, ms, model, progress_cb=None):
    to_realign, chunks, start_idx, end_idx = prepare_multipass(alignment)
    tasks = []

    def realign(chunk):
        realignments = []
        wavfile = wave.open(sys.argv[1], "rb")
        if chunk[0].start is None:
            start_t = 0
        else:
            start_t = chunk[0].start
        if chunk[-1].end is None:
            end_t = wavfile.getnframes() / float(wavfile.getframerate())
        else:
            end_t = chunk[-1].end

        duration = end_t - start_t
        chunk_start_word = chunk[0].word
        chunk_end_word = chunk[-1].word

        # Create a language model
        task_start = chunk[0].startOffset
        task_end = chunk[-1].endOffset
        task_transcript = ms.raw_sentence[task_start:task_end]
        task_ms = metasentence.MetaSentence(task_transcript, model)
        task_ks = task_ms.get_kaldi_sequence()
        seq_length = len(task_ks)
        task_recognizer = language_model.make_bigram_language_model(task_transcript + '.', model)
        start_pos = int(((start_t-0.6) * wavfile.getframerate()))
        wavfile.setpos(start_pos)
        end_pos = int((duration+1) * wavfile.getframerate())
        chunk_end = end_pos + start_pos
        words = transcriber.transcribe(task_recognizer, wavfile, chunk_end, duration)[0][0:seq_length+1]

        if words[0]['word'] != chunk_start_word:
            words = words[1:len(words)]
        if words[-1]['word'] != chunk_end_word:
            words = words[0:len(words)-1]

        word_alignment = diff_align.align(words, task_ms)

        for w in word_alignment:
            w.shift(time=start_t, offset=task_start)

        realignments.append({"chunk": chunk, "words": word_alignment})

        if progress_cb is not None:
            progress_cm({"percent": len(realignments) / float(len(to_realign))})
        return realignments

    for i in range(chunks):
        tasks.extend(realign(to_realign[i]))

    output_words = alignment
    for i, ret in enumerate(tasks):
        output_words = output_words[:start_idx[i]] + ret['words'][0:-1] + output_words[end_idx[i]:]

    return output_words
