#!/usr/bin/env python3

import json
import gradio as gr

from vosk import KaldiRecognizer, Model

model = Model(lang="en-us")

def transcribe(data, state):
    sample_rate, audio_data = data
    audio_data = (audio_data >> 16).astype("int16").tobytes()

    if state is None:
        rec = KaldiRecognizer(model, sample_rate)
        result = []
    else:
        rec, result = state

    if rec.AcceptWaveform(audio_data):
        text_result = json.loads(rec.Result())["text"]
        if text_result != "":
            result.append(text_result)
        partial_result = ""
    else:
        partial_result = json.loads(rec.PartialResult())["partial"] + " "

    return "\n".join(result) + "\n" + partial_result, (rec, result)

gr.Interface(
    fn=transcribe,
    inputs=[
        gr.Audio(source="microphone", type="numpy", streaming=True),
        "state"
    ],
    outputs=[
        "textbox",
        "state"
    ],
    live=True).launch(share=True)
