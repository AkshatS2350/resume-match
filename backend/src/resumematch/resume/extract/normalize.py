"""The fixed canonical text-normalization pipeline."""

import re
import unicodedata

_LIGATURES = str.maketrans(
    {"ﬁ": "fi", "ﬂ": "fl", "ﬀ": "ff", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "ft", "ﬆ": "st"}
)
_SPACES = str.maketrans({character: " " for character in "\u00a0\u2007\u202f\u2009\u200a"})
_PUNCTUATION = str.maketrans(
    {**{character: "-" for character in "‐‑‒–—―"}, "‘": "'", "’": "'", "“": '"', "”": '"'}
)


def normalize(value: str) -> str:
    value = unicodedata.normalize("NFKC", value).translate(_LIGATURES).translate(_SPACES)
    value = value.translate(_PUNCTUATION).replace("\r\n", "\n").replace("\r", "\n")
    value = re.sub(r" {2,}", " ", value)
    value = "\n".join(line.rstrip() for line in value.split("\n"))
    return re.sub(r"\n{3,}", "\n\n", value)
