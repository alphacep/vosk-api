# phoneme_feedback_kiddo.py
# Educational Example – Vosk + CMU Pronouncing Dictionary for Pronunciation Feedback
# Author: Aparna V Sunil

import os
import wave
import json
import nltk
from vosk import Model, KaldiRecognizer
from nltk.corpus import cmudict

# Ensure CMU dictionary is downloaded
nltk.download('cmudict')
pron_dict = cmudict.dict()

# Setup Vosk model path
MODEL_PATH = "model"  # Replace with your actual model folder name (e.g., vosk-model-en-us-0.22)
AUDIO_FILE = "test.wav"  # Replace with a .wav file of a child saying the target word

# Target word expected from child
TARGET_WORD = "elephant"

# Load expected phonemes
expected_phonemes = pron_dict.get(TARGET_WORD.lower(), [[]])[0]
expected_clean = [p.strip("0123456789").lower() for p in expected_phonemes]

print(f"\n🎯 Target Word: {TARGET_WORD}")
print(f"✅ Expected Phonemes: {expected_clean}")

# Initialize Vosk recognizer
if not os.path.exists(MODEL_PATH):
    print(f"❌ Vosk model not found at: {MODEL_PATH}")
    exit(1)

model = Model(MODEL_PATH)
wf = wave.open(AUDIO_FILE, "rb")

if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
    print("❌ Audio file must be WAV 16KHz Mono PCM.")
    exit(1)

recognizer = KaldiRecognizer(model, wf.getframerate())

# Run speech recognition
recognized_text = ""
while True:
    data = wf.readframes(4000)
    if len(data) == 0:
        break
    if recognizer.AcceptWaveform(data):
        result = json.loads(recognizer.Result())
        recognized_text += result.get("text", "") + " "

recognized_text = recognized_text.strip().lower()
print(f"\n🎙️ Recognized Speech: {recognized_text}")

# Extract recognized phonemes
recognized_phonemes = []
for word in recognized_text.split():
    phones = pron_dict.get(word.lower())
    if phones:
        recognized_phonemes.extend(phones[0])

recognized_clean = [p.strip("0123456789").lower() for p in recognized_phonemes]

print(f"🗣️ Recognized Phonemes: {recognized_clean}")

# Compare phonemes
print("\n📌 Phoneme Feedback:")
matched = set(expected_clean).intersection(set(recognized_clean))
missing = list(set(expected_clean) - set(recognized_clean))

for phoneme in expected_clean:
    if phoneme in matched:
        print(f"✅ {phoneme}")
    else:
        print(f"❌ Missing or incorrect: {phoneme}")

similarity = len(matched) / len(expected_clean) if expected_clean else 0
print(f"\n🔎 Similarity Score: {similarity:.2f}")

if similarity == 1.0:
    print("🎉 Perfect pronunciation!")
elif similarity >= 0.6:
    print("👍 Good attempt, but some phonemes need work.")
else:
    print("❗ Needs improvement. Try again!")
