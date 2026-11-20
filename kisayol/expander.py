"""Bir eşleşmeyi uygular: tetikleyiciyi siler, metni yapıştırır ya da yazar, panoyu geri yükler."""
from __future__ import annotations

import time
from datetime import datetime
from typing import Callable, Optional

try:
    from typing import Protocol
except ImportError:  # pragma: no cover
    Protocol = object

from . import clipboard as _clipboard
from .matcher import Match
from .variables import resolve

MODIFIER_KEYS = ("shift", "ctrl", "alt", "windows")
MODIFIER_WAIT = 0.5
POLL = 0.01


class KeySink(Protocol):
    def tap(self, key: str) -> None: ...
    def write(self, text: str, delay_ms: int) -> None: ...
    def release(self, key: str) -> None: ...
    def is_pressed(self, key: str) -> bool: ...


class Expander:
    def __init__(self, sink: KeySink, clip=_clipboard, settings: Optional[dict] = None,
                 sleep: Callable[[float], None] = time.sleep,
                 now: Callable[[], datetime] = datetime.now):
        self.sink = sink
        self.clip = clip
        self.settings = settings if settings is not None else {}
        self.sleep = sleep
        self.now = now

    def _setting(self, key, default):
        return self.settings.get(key, default)

    def _release_modifiers(self) -> None:
        waited = 0.0
        while waited < MODIFIER_WAIT and any(self.sink.is_pressed(k) for k in MODIFIER_KEYS):
            self.sleep(POLL)
            waited += POLL
        for k in MODIFIER_KEYS:
            if self.sink.is_pressed(k):
                self.sink.release(k)

    def _type(self, text: str) -> None:
        delay = int(self._setting("type_delay_ms", 2))
        lines = text.split("\n")
        for i, line in enumerate(lines):
            if i:
                self.sink.tap("shift+enter")
            if line:
                self.sink.write(line, delay)

    def _clip_text(self) -> str:
        try:
            return self.clip.get_text()
        except Exception:
            return ""

    def expand(self, match: Match) -> None:
        self._release_modifiers()
        for _ in range(match.delete_count):
            self.sink.tap("backspace")

        snippet = match.snippet
        uses_clip = "{pano}" in snippet.text or "{clipboard}" in snippet.text
        text, cursor_left = resolve(
            snippet.text, self.now(), self._clip_text() if uses_clip else "",
            self._setting("date_fmt", "%d.%m.%Y"), self._setting("time_fmt", "%H:%M"))

        saved = None
        if text:
            if snippet.method == "paste":
                try:
                    saved = self.clip.backup()
                    self.clip.set_text(text)
                except Exception:
                    if saved is not None:
                        try:
                            self.clip.restore(saved)
                        except Exception:
                            pass
                    saved = None
                    self._type(text)
                else:
                    self.sink.tap("ctrl+v")
            else:
                self._type(text)

        if match.suffix:
            self.sink.write(match.suffix, 0)
        if cursor_left is not None:
            for _ in range(cursor_left + len(match.suffix)):
                self.sink.tap("left")

        if saved is not None:
            self.sleep(int(self._setting("restore_delay_ms", 150)) / 1000.0)
            try:
                self.clip.restore(saved)
            except Exception:
                pass
