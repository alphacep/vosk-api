#!/usr/bin/env python3

import json
import gradio as gr

from vosk import KaldiRecognizer, Model

model = Model(lang="en-us")

def transcribe(stream, new_chunk, transcribe_speaker, transcribe_meeting):

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

def start_transcription():
    return None, ""

def stop_transcription(stream):
    if stream is not None:
        rec, result = stream
        final_result = json.loads(rec.FinalResult())["text"]
        result.append(final_result)
        return None, "\n".join(result)
    return None, ""

with gr.Blocks() as demo:
    transcribe_speaker = gr.Checkbox(label="Transcribe Speaker's Voice")
    transcribe_meeting = gr.Checkbox(label="Transcribe Entire Meeting")
    start_button = gr.Button("Start Transcription")
    stop_button = gr.Button("Stop Transcription")
    state = gr.State()
    audio = gr.Audio(sources=["microphone"], type="numpy", streaming=True)
    text = gr.Textbox()

    start_button.click(start_transcription, inputs=[], outputs=[state, text])
    stop_button.click(stop_transcription, inputs=[state], outputs=[state, text])
    audio.change(transcribe, inputs=[state, audio, transcribe_speaker, transcribe_meeting], outputs=[state, text])

demo.launch(share=True)
