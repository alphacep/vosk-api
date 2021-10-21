import logging
import wave

from . import metasentence
from . import language_model
from . import diff_align
from . import transcription
'''
The script will rework
Multipass realign unaligned words.
Prepare multipass checking words sequence, when word's case == 
not-found-in-audio preparing chunk to realign like [words before, unaligned 
words, words after], creating new personal small language and acoustic models
for the chunk putting back into result sequence.
'''
def prepare_multipass(alignment):
    cur_unaligned_words = []
    to_realign = []
    prev_words = []
    next_words = []
    unite = False

    for i, w in enumerate(alignment):
        if w.not_found_in_audio(): # 39=resonant/69=resonant
            if cur_unaligned_words == []: # if 1-st word(opening)
                start_idx = i # 39/69
                for j in range(max(0, start_idx - 3), start_idx): # 36/66(i-3)
                    if alignment[j].not_found_in_audio(): # 36-38/66-68
                        unite = True # if left word has case NFIA then True
                cur_unaligned_words.append(w) # collect all NFIA 1st-last
        elif w.success(): # mark 1st case success after NFIA 
            if len(cur_unaligned_words) > 0: # True cuz c_u_w has words
                end_idx = i # 40/70
# add 0 to -3 words left and 0 to +3 words right sides:
                prev_words = alignment[max(0, start_idx - 3):end_idx-1:1]
                prev_len = len(prev_words) # len of left words[0,1,2,3?]
                next_words = alignment[start_idx + 1:min(len(alignment), end_idx + 3):1]
                next_len = len(next_words) # len of right words[0,1,2,3?]
                if unite == False: # if left side hasn't 3 words NFIA
                    to_realign.append({ # collect current task into to_realign
                        "start": prev_words,
                        "end": next_words,
                        "words": cur_unaligned_words})
                else: # elif left side has NFIA case words between 3 words 
                    add_part = cur_unaligned_words + next_words
                    to_realign[len(to_realign) - 1]["end"] = to_realign[len(to_realign) - 1]["end"] + add_part # chaning end of last task to end+add_part
                    unite = False # change flag on False that check again
                cur_unaligned_words = []
    return to_realign, prev_len, next_len

def realign(wavfile, alignment, amount, ms, transcriber, model, progress_cb=None):
    to_realign, prev_len, next_len = prepare_multipass(alignment)
    realignments = []

    def realign(chunk):
        if chunk["start"] is None:
            start_t = 0
        else:
            start_t = chunk["start"][0].start
        if chunk["end"] is None:
            end_t = wavfile.getnframes() / float(wavfile.getframerate())
        else:
            end_t = chunk["end"][len(chunk["end"])-1].end
        duration = end_t - start_t
        if duration < 0.75 or duration > 60:
            logging.debug("cannot realign %d words with duration %f" % (len(chunk['words']), duration))
            return
        
        # Create a language model
        task_start = chunk["start"][0].startOffset
        task_end = chunk["end"][-1].endOffset
        task_transcript = ms.raw_sentence[task_start:task_end]
        task_ms = metasentence.MetaSentence(task_transcript, model)
        task_ks = task_ms.get_kaldi_sequence()
        seq_length = len(task_ks)
        task_gen_hclg_filename = language_model.make_bigram_language_model(task_transcript + '.', model)
        wavfile.setpos(int((start_t - 0.4) * wavfile.getframerate()))
        ret = transcriber.transcribe(wavfile, duration)[0][0:seq_length]
        word_alignment = diff_align.align(ret, task_ms)

        for w in word_alignment:
            w.shift(time=start_t, offset=task_start)

        realignments.append({"chunk": chunk, "words": word_alignment})

        if progress_cb is not None:
            progress_cm({"percent": len(realignments) / float(len(to_realign))})
    for chunks in range(amount):
        chunk = to_realign[chunks]
        ret = realign(chunk)

    # Sub in the replacements
    o_words = alignment
    for ret in realignments:
        st_idx = o_words.index(ret["chunk"]["words"][0])
        end_idx= o_words.index(ret["chunk"]["words"][-1])+1
        o_words = o_words[:st_idx-prev_len] + ret["words"] + o_words[end_idx+next_len:]
    return o_words
