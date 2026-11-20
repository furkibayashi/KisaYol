"""Win32 panosu (ctypes): metin okuma/yazma ve tüm HGLOBAL biçimlerini yedekleme/geri yükleme."""
from __future__ import annotations

import ctypes
import sys
import time
from ctypes import wintypes
from typing import List, Tuple

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002
# HGLOBAL olmayan (GDI tutamaçlı) ya da sahibine bağlı biçimler: kopyalanamaz, atlanır
SKIP_FORMATS = frozenset({2, 3, 9, 14, 0x80, 0x82, 0x83, 0x8E})
OPEN_TRIES = 10
OPEN_WAIT = 0.02


class ClipboardError(Exception):
    pass


if sys.platform == "win32":
    _u = ctypes.WinDLL("user32", use_last_error=True)
    _k = ctypes.WinDLL("kernel32", use_last_error=True)

    _u.OpenClipboard.argtypes = [wintypes.HWND]
    _u.OpenClipboard.restype = wintypes.BOOL
    _u.CloseClipboard.restype = wintypes.BOOL
    _u.EmptyClipboard.restype = wintypes.BOOL
    _u.EnumClipboardFormats.argtypes = [wintypes.UINT]
    _u.EnumClipboardFormats.restype = wintypes.UINT
    _u.GetClipboardData.argtypes = [wintypes.UINT]
    _u.GetClipboardData.restype = wintypes.HANDLE
    _u.SetClipboardData.argtypes = [wintypes.UINT, wintypes.HANDLE]
    _u.SetClipboardData.restype = wintypes.HANDLE
    _u.CreateWindowExW.argtypes = [wintypes.DWORD, wintypes.LPCWSTR, wintypes.LPCWSTR, wintypes.DWORD,
                                   ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                                   wintypes.HWND, wintypes.HMENU, wintypes.HINSTANCE, wintypes.LPVOID]
    _u.CreateWindowExW.restype = wintypes.HWND

    _k.GlobalAlloc.argtypes = [wintypes.UINT, ctypes.c_size_t]
    _k.GlobalAlloc.restype = wintypes.HGLOBAL
    _k.GlobalLock.argtypes = [wintypes.HGLOBAL]
    _k.GlobalLock.restype = ctypes.c_void_p
    _k.GlobalUnlock.argtypes = [wintypes.HGLOBAL]
    _k.GlobalUnlock.restype = wintypes.BOOL
    _k.GlobalSize.argtypes = [wintypes.HGLOBAL]
    _k.GlobalSize.restype = ctypes.c_size_t
    _k.GlobalFree.argtypes = [wintypes.HGLOBAL]
    _k.GlobalFree.restype = wintypes.HGLOBAL

_hwnd = None


def _owner():
    """EmptyClipboard'un sahibi NULL olmasın diye gizli, yalnızca mesaj alan bir pencere."""
    global _hwnd
    if _hwnd is None:
        HWND_MESSAGE = wintypes.HWND(-3)
        _hwnd = _u.CreateWindowExW(0, "STATIC", "KisaYolClipboard", 0, 0, 0, 0, 0,
                                   HWND_MESSAGE, None, None, None)
    return _hwnd


class _Open:
    def __enter__(self):
        owner = _owner()
        for _ in range(OPEN_TRIES):
            if _u.OpenClipboard(owner):
                return self
            time.sleep(OPEN_WAIT)
        raise ClipboardError("pano açılamadı (başka bir uygulama kullanıyor)")

    def __exit__(self, *exc):
        _u.CloseClipboard()
        return False


def _read_handle(h) -> bytes:
    size = _k.GlobalSize(h)
    ptr = _k.GlobalLock(h)
    if not ptr:
        raise ClipboardError("pano verisi kilitlenemedi")
    try:
        return ctypes.string_at(ptr, size)
    finally:
        _k.GlobalUnlock(h)


def _set(fmt: int, data: bytes) -> None:
    h = _k.GlobalAlloc(GMEM_MOVEABLE, max(len(data), 1))
    if not h:
        raise ClipboardError("bellek ayrılamadı")
    ptr = _k.GlobalLock(h)
    if not ptr:
        _k.GlobalFree(h)
        raise ClipboardError("bellek kilitlenemedi")
    ctypes.memmove(ptr, data, len(data))
    _k.GlobalUnlock(h)
    if not _u.SetClipboardData(fmt, h):
        _k.GlobalFree(h)   # başarısızsa sahiplik bizde kalır
        raise ClipboardError("SetClipboardData başarısız")


def get_text() -> str:
    with _Open():
        h = _u.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        raw = _read_handle(h)
    text = raw.decode("utf-16-le", errors="replace")
    return text.split("\x00", 1)[0].replace("\r\n", "\n")


def set_text(s: str) -> None:
    data = s.replace("\r\n", "\n").replace("\n", "\r\n").encode("utf-16-le") + b"\x00\x00"
    with _Open():
        _u.EmptyClipboard()
        _set(CF_UNICODETEXT, data)


def backup() -> List[Tuple[int, bytes]]:
    items = []
    with _Open():
        fmt = _u.EnumClipboardFormats(0)
        while fmt:
            if fmt not in SKIP_FORMATS:
                h = _u.GetClipboardData(fmt)
                if h:
                    try:
                        items.append((fmt, _read_handle(h)))
                    except ClipboardError:
                        pass
            fmt = _u.EnumClipboardFormats(fmt)
    return items


def restore(data: List[Tuple[int, bytes]]) -> None:
    with _Open():
        _u.EmptyClipboard()
        for fmt, raw in data:
            try:
                _set(fmt, raw)
            except ClipboardError:
                pass
