"""Sistem tepsisi simgesi (pystray, kendi iş parçacığında). Olayları arayüze yalnızca post() ile iletir."""
from __future__ import annotations

import os
import sys

from PIL import Image, ImageDraw

from .i18n import T


def _asset(name: str) -> str:
    for base in (getattr(sys, "_MEIPASS", ""), os.path.dirname(os.path.dirname(os.path.abspath(__file__)))):
        path = os.path.join(base, "assets", name)
        if base and os.path.exists(path):
            return path
    return ""


def icon_image(accent: str = "#7c5cff") -> Image.Image:
    path = _asset("icon.png")
    if path:
        try:
            return Image.open(path).convert("RGBA").resize((64, 64), Image.LANCZOS)
        except Exception:
            pass
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.rounded_rectangle((2, 2, 62, 62), radius=14, fill=accent)
    d.text((22, 14), "K", fill="white")
    return img


def dimmed(img: Image.Image) -> Image.Image:
    out = img.copy()
    alpha = out.getchannel("A").point(lambda a: int(a * 0.4))
    out.putalpha(alpha)
    return out


class Tray:
    def __init__(self, post, accent: str, paused: bool):
        self.post = post
        self.paused = paused
        self._base = icon_image(accent)
        self._icon = None

    def _menu(self):
        import pystray
        return pystray.Menu(
            pystray.MenuItem(T("tray_open"), lambda: self.post(("tray", "open")), default=True),
            pystray.MenuItem(lambda _i: T("tray_resume") if self.paused else T("tray_pause"),
                             lambda: self.post(("tray", "pause"))),
            pystray.MenuItem(T("tray_quit"), lambda: self.post(("tray", "quit"))),
        )

    def start(self) -> None:
        try:
            import pystray
            self._icon = pystray.Icon("KisaYol", self._image(), "KısaYol", self._menu())
            self._icon.run_detached()
        except Exception:
            self._icon = None

    def _image(self):
        return dimmed(self._base) if self.paused else self._base

    def set_paused(self, paused: bool) -> None:
        self.paused = paused
        if self._icon:
            try:
                self._icon.icon = self._image()
                self._icon.update_menu()
            except Exception:
                pass

    def refresh_language(self) -> None:
        if self._icon:
            try:
                self._icon.menu = self._menu()
                self._icon.update_menu()
            except Exception:
                pass

    def stop(self) -> None:
        if self._icon:
            try:
                self._icon.stop()
            except Exception:
                pass
