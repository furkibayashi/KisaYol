"""Kalıp arama (arayüzdeki liste ve arama penceresi için). Saf Python."""
from __future__ import annotations

from typing import List

from .snippets import Snippet


def fold(s: str) -> str:
    """Türkçe duyarlı büyük/küçük harf katlama: İ→i, I→ı."""
    return s.replace("İ", "i").replace("I", "ı").casefold()


def filter_snippets(snippets: List[Snippet], query: str) -> List[Snippet]:
    q = fold(query.strip())
    if not q:
        return list(snippets)
    by_trigger = [s for s in snippets if q in fold(s.trigger)]
    by_text = [s for s in snippets if s not in by_trigger and q in fold(s.text)]
    return by_trigger + by_text
