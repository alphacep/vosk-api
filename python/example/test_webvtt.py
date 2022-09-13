#!/usr/bin/env python3

import sys
import subprocess
import json
import textwrap

from webvtt import WebVTT, Caption
from vosk import Model, KaldiRecognizer, SetLogLevel

SAMPLE_RATE = 16000
WORDS_PER_LINE = 7

SetLogLevel(-1)

model = Model(lang="en-us")
rec = KaldiRecognizer(model, SAMPLE_RATE)
rec.SetWords(True)


def timestring(seconds):
    minutes = seconds / 60
    seconds = seconds % 60
    hours = int(minutes / 60)
    minutes = int(minutes % 60)
    return "%i:%02i:%06.3f" % (hours, minutes, seconds)


def transcribe():
    command = ["ffmpeg", "-nostdin", "-loglevel", "quiet", "-i", sys.argv[1],
               "-ar", str(SAMPLE_RATE), "-ac", "1", "-f", "s16le", "-"]
    with subprocess.Popen(command, stdout=subprocess.PIPE) as process:

        results = []
        while True:
            data = process.stdout.read(4000)
            if len(data) == 0:
                break
            if rec.AcceptWaveform(data):
                results.append(rec.Result())
        results.append(rec.FinalResult())

        vtt = WebVTT()
        for _, res in enumerate(results):
            words = json.loads(res).get("result")
            if not words:
                continue

            start = timestring(words[0]["start"])
            end = timestring(words[-1]["end"])
            content = " ".join([w["word"] for w in words])

            caption = Caption(start, end, textwrap.fill(content))
            vtt.captions.append(caption)

        # save or return webvtt
        if len(sys.argv) > 2:
            vtt.save(sys.argv[2])
        else:
            print(vtt.content)


if __name__ == "__main__":
    if not 1 < len(sys.argv) < 4:
        print("Usage: {} audiofile [output file]".format(sys.argv[0]))
        sys.exit(1)
    transcribe()
