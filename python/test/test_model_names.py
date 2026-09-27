import importlib.util
import unittest
from pathlib import Path

# Load the matcher without importing the native recognizer.
_path = Path(__file__).resolve().parents[1] / "vosk" / "model_names.py"
_spec = importlib.util.spec_from_file_location("model_names", _path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
model_name_matches_lang = _mod.model_name_matches_lang


class TestModelNameMatchesLang(unittest.TestCase):
    def test_arabic_does_not_select_tunisian(self):
        tunisian = "vosk-model-small-ar-tn-0.1-linto"
        arabic = "vosk-model-small-ar-0.3"
        self.assertFalse(model_name_matches_lang(tunisian, "ar"))
        self.assertTrue(model_name_matches_lang(arabic, "ar"))
        self.assertTrue(model_name_matches_lang(tunisian, "ar-tn"))

    def test_other_language_names_still_match(self):
        self.assertTrue(model_name_matches_lang("vosk-model-pt-fb-v0.1.1-pruned", "pt"))
        self.assertTrue(model_name_matches_lang("vosk-model-small-en-us-0.15", "en-us"))
        self.assertFalse(model_name_matches_lang("vosk-model-en-in-0.5", "en-us"))
        self.assertTrue(
            model_name_matches_lang("vosk-model-nl-spraakherkenning-0.6", "nl")
        )
