from __future__ import annotations

import re
import unicodedata


def normalize_text(text: str) -> str:
    lowered = text.lower().strip()
    normalized = unicodedata.normalize('NFKD', lowered)
    return ''.join(ch for ch in normalized if not unicodedata.combining(ch))


def tokenize(text: str) -> list[str]:
    normalized = normalize_text(text)
    return [token for token in re.findall(r'\w+', normalized) if len(token) > 1]

