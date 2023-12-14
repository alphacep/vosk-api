#!/usr/bin/env python3

import json
import gradio as gr

from vosk import KaldiRecognizer, Model

model = Model(lang="en-us")

def transcribe(stream, new_chunk):

    sample_rate, audio_data = new_chunk
    audio_data = audio_data.tobytes()

    if stream is None:
        rec = KaldiRecognizer(model, sample_rate)
        result = []
    else:
        rec, result = stream

    if rec.AcceptWaveform(audio_data):
        text_result = json.loads(rec.Result())["text"]
        if text_result != "":
            result.append(text_result)
        partial_result = ""
    else:
        partial_result = json.loads(rec.PartialResult())["partial"] + " "

    return (rec, result), "\n".join(result) + "\n" + partial_result

gr.Interface(
    fn=transcribe,
    inputs=[
        "state", gr.Audio(sources=["microphone"], type="numpy", streaming=True),
    ],
    outputs=[
        "state", "text",
    ],
    live=True).launch(share=True)
