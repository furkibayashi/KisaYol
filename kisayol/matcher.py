"""Tuş tamponu ve tetikleyici eşleştirme (karma kural). Saf Python; Windows'a dokunmaz."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from .snippets import Snippet, is_symbol_trigger

TERMINATORS = frozenset(" .,!?:;)]}\"'")
BUFFER_MAX = 64


@dataclass
class Match:
    snippet: Snippet
    delete_count: int
    suffix: str


class Matcher:
    def __init__(self):
        self._buf = ""
        self._truncated = False   # tampon baştan kırpıldıysa ilk kelime gerçek kelime başı değildir
        self._symbol: List[Snippet] = []
        self._bare: Dict[str, Snippet] = {}

    @property
    def buffer(self) -> str:
        return self._buf

    def set_snippets(self, snippets: List[Snippet]) -> None:
        active = [s for s in snippets if s.enabled]
        self._symbol = sorted((s for s in active if is_symbol_trigger(s.trigger)),
                              key=lambda s: len(s.trigger), reverse=True)
        self._bare = {s.trigger: s for s in active if not is_symbol_trigger(s.trigger)}

    def reset(self) -> None:
        self._buf = ""
        self._truncated = False

    def backspace(self) -> None:
        self._buf = self._buf[:-1]

    def feed(self, ch: str) -> Optional[Match]:
        self._buf += ch
        if len(self._buf) > BUFFER_MAX:
            self._buf = self._buf[-BUFFER_MAX:]
            self._truncated = True

        for s in self._symbol:                      # en uzun önce
            if self._buf.endswith(s.trigger):
                self.reset()
                return Match(s, len(s.trigger), "")

        if ch in TERMINATORS and self._bare:
            head = self._buf[:-1]
            i = len(head)
            while i > 0 and head[i - 1].isalnum():
                i -= 1
            word = head[i:]
            at_start = not (i == 0 and self._truncated)
            s = self._bare.get(word) if word and at_start else None
            if s is not None:
                self.reset()
                return Match(s, len(word) + 1, ch)
        return None
