"""Match a local Vosk model directory to a language code."""

from re import match

# A directory for a more specific language is not a model for the shorter code.
# vosk-model-small-ar-tn-0.1-linto is Tunisian Arabic, not Arabic.
_LONGER_LANGS = ("ar-tn",)


def model_name_matches_lang(model_name, lang):
    """Return true when `model_name` is a model for `lang`.

    The language code has to end at a hyphen. A longer code that continues
    it, such as ar-tn, is a different language.
    """
    found = match(r"vosk-model(?:-small)?-(.+)", model_name)
    if not found:
        return False
    body = found.group(1)
    if body != lang and not body.startswith(lang + "-"):
        return False
    for longer in _LONGER_LANGS:
        if longer == lang or not longer.startswith(lang + "-"):
            continue
        if body == longer or body.startswith(longer + "-"):
            return False
    return True
