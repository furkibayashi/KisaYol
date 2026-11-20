"""Kalıp metnindeki {tarih}, {saat}, {pano}, {imleç} değişkenlerini çözer."""
from __future__ import annotations

from datetime import datetime
from typing import Optional, Tuple

DATE_NAMES = ("tarih", "date")
TIME_NAMES = ("saat", "time")
CLIP_NAMES = ("pano", "clipboard")
CURSOR_NAMES = ("imleç", "cursor")
_CURSOR = object()


def _format(now: datetime, fmt: str) -> Optional[str]:
    try:
        return now.strftime(fmt)
    except (ValueError, TypeError):
        return None


def _token(body: str, now: datetime, clipboard: str, date_fmt: str, time_fmt: str):
    """Değişken gövdesinin değeri; tanınmazsa None, imleçse _CURSOR."""
    name, sep, fmt = body.partition(":")
    if name in CURSOR_NAMES and not sep:
        return _CURSOR
    if name in CLIP_NAMES and not sep:
        return clipboard
    if name in DATE_NAMES:
        return _format(now, fmt if sep else date_fmt)
    if name in TIME_NAMES:
        return _format(now, fmt if sep else time_fmt)
    return None


def resolve(text: str, now: datetime, clipboard: str,
            date_fmt: str = "%d.%m.%Y", time_fmt: str = "%H:%M") -> Tuple[str, Optional[int]]:
    """(son metin, imleçten sonra kalan karakter sayısı ya da imleç yoksa None)."""
    text = text.replace("\r\n", "\n")
    out = []
    cursor_at: Optional[int] = None
    i, n = 0, len(text)
    while i < n:
        ch = text[i]
        if ch == "{" and text.startswith("{{", i):
            out.append("{")
            i += 2
            continue
        if ch == "}" and text.startswith("}}", i):
            out.append("}")
            i += 2
            continue
        if ch == "{":
            end = text.find("}", i + 1)
            if end != -1:
                value = _token(text[i + 1:end], now, clipboard, date_fmt, time_fmt)
                if value is _CURSOR:
                    if cursor_at is None:
                        cursor_at = sum(len(p) for p in out)
                    i = end + 1
                    continue
                if value is not None:
                    out.append(value)
                    i = end + 1
                    continue
        out.append(ch)
        i += 1
    result = "".join(out)
    return result, (None if cursor_at is None else len(result) - cursor_at)
