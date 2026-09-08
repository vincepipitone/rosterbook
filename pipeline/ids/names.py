"""Name normalization for joining human-maintained lists (AZ Phil, MLBTR) to MLBAM ids.

Always normalize BOTH sides. Accents stripped, suffixes (Jr/Sr/II/III) and punctuation dropped.
"""
from __future__ import annotations

import re
import unicodedata

SUFFIX = re.compile(r"\b(jr|sr|ii|iii|iv)\b\.?", re.I)


def normalize(name: str) -> str:
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode()
    s = s.lower().replace(".", " ").replace("-", " ").replace("'", "")
    s = SUFFIX.sub(" ", s)
    s = re.sub(r"[^a-z ]", " ", s)
    return " ".join(s.split())


# Manual aliases (normalized target -> normalized source) when sources spell names differently.
ALIASES = {
    "b j murray": "bj murray",
}


def key(name: str) -> str:
    n = normalize(name)
    return ALIASES.get(n, n)
