"""Uygulama ayarları: yükleme, tip kontrollü birleştirme, atomik ve gecikmeli kayıt."""
from __future__ import annotations

import copy
import json
import os
import sys
import threading

from . import APP_ID


def config_dir() -> str:
    base = os.environ.get("APPDATA") or os.path.expanduser("~")
    path = os.path.join(base, APP_ID)
    os.makedirs(path, exist_ok=True)
    return path


def app_dir() -> str:
    """Exe ya da betiğin bulunduğu klasör."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


DEFAULTS = {
    "app": {
        "language": "",          # boş = sistem dilinden algıla
        "theme": "midnight",
        "accent": "",
        "sound": False,
        "osd": True,
        "pause_hotkey": "ctrl+alt+p",
        "search_hotkey": "ctrl+alt+space",
        "date_fmt": "%d.%m.%Y",
        "time_fmt": "%H:%M",
        "type_delay_ms": 2,
        "restore_delay_ms": 150,
        "autostart": False,
        "geometry": "",
        "paused": False,
        "ui_scale": 1.0,
    },
    "stats": {
        "expansions": 0,
    },
}


def _merge(base, extra):
    """extra içindeki geçerli anahtarları base'in üzerine yazar (tip kontrolüyle). OtoTık'tan."""
    for key, val in extra.items():
        if key not in base:
            continue
        if isinstance(base[key], dict) and isinstance(val, dict):
            _merge(base[key], val)
        elif isinstance(base[key], bool):
            base[key] = bool(val)
        elif isinstance(base[key], (int, float)) and not isinstance(val, bool) and isinstance(val, (int, float)):
            base[key] = type(base[key])(val) if isinstance(base[key], int) and float(val).is_integer() else val
        elif isinstance(base[key], type(val)) or base[key] in ("", None) or isinstance(base[key], list):
            base[key] = val
    return base


class Config:
    def __init__(self, path: str):
        self.path = path
        self.data = copy.deepcopy(DEFAULTS)
        self._lock = threading.RLock()
        self._save_timer = None
        self.first_run = not os.path.exists(path)
        self.load()

    def __getitem__(self, section):
        return self.data[section]

    def get(self, section, key):
        return self.data[section][key]

    def set(self, section, key, value):
        self.data[section][key] = value
        self.save_later()

    def load(self) -> None:
        if not os.path.exists(self.path):
            return
        try:
            with open(self.path, "r", encoding="utf-8-sig") as f:
                loaded = json.load(f)
            if isinstance(loaded, dict):
                _merge(self.data, loaded)
        except Exception:
            pass
        app = self.data["app"]
        for key in ("type_delay_ms", "restore_delay_ms"):
            if app[key] < 0:
                app[key] = DEFAULTS["app"][key]

    def save(self) -> None:
        with self._lock:
            tmp = self.path + ".tmp"
            try:
                with open(tmp, "w", encoding="utf-8") as f:
                    json.dump(self.data, f, ensure_ascii=False, indent=2)
                os.replace(tmp, self.path)
            except Exception:
                pass

    def save_later(self, delay: float = 1.0) -> None:
        if self._save_timer:
            self._save_timer.cancel()
        self._save_timer = threading.Timer(delay, self.save)
        self._save_timer.daemon = True
        self._save_timer.start()
