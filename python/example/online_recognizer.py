#!/usr/bin/env python3

from vosk import KaldiRecognizer, Model
import gradio as gr
import json

result = []
model = Model(lang="en-us")

def transcribe(data, rec):
    text = ''
    sample_rate, stream = data
    stream = (stream >> 16).astype("int16")
    if rec is None:
        rec = KaldiRecognizer(model, sample_rate)
    if rec.AcceptWaveform(stream.tobytes()):
        text = json.loads(rec.Result())["text"] + " "
        result.append(text)
    else:
        text = json.loads(rec.PartialResult())["partial"] + " "
    return '\n'.join(result) + '\n' + text, rec

gr.Interface(
    fn=transcribe,
    inputs=[
        gr.Audio(source="microphone", type="numpy", streaming=True),
        "state"
    ],
    outputs=[
        "textbox",
        "state",
    ],
    live=True).launch(share=True)
