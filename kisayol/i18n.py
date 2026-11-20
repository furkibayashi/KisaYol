"""Çoklu dil desteği. Eksik çeviriler İngilizceye düşer."""
import locale
import sys

LANGUAGES = [
    ("tr", "Türkçe"),
    ("en", "English"),
    ("de", "Deutsch"),
    ("es", "Español"),
    ("fr", "Français"),
    ("pt", "Português"),
    ("ru", "Русский"),
]

STRINGS = {code: {} for code, _ in LANGUAGES}

STRINGS["en"].update({
    "nav_snippets": "Snippets", "nav_settings": "Settings", "nav_about": "About",
    "snippet_count": "{n} snippets",
})

STRINGS["tr"].update({
    "nav_snippets": "Kalıplar", "nav_settings": "Ayarlar", "nav_about": "Hakkında",
    "snippet_count": "{n} kalıp",
})

_current = "en"


def set_language(code):
    global _current
    _current = code if code in STRINGS else "en"


def get_language():
    return _current


def T(key, **kw):
    s = STRINGS.get(_current, {}).get(key) or STRINGS["en"].get(key) or key
    if kw:
        try:
            return s.format(**kw)
        except (KeyError, IndexError, ValueError):
            return s
    return s


def detect_language():
    code = ""
    if sys.platform.startswith("win"):
        try:
            import ctypes
            lid = ctypes.windll.kernel32.GetUserDefaultUILanguage()
            code = {0x1F: "tr", 0x09: "en", 0x07: "de", 0x0A: "es", 0x0C: "fr",
                    0x16: "pt", 0x19: "ru"}.get(lid & 0x3FF, "")
        except Exception:
            pass
    if not code:
        try:
            loc = (locale.getlocale()[0] or "").lower()
            code = loc[:2]
        except Exception:
            pass
    return code if code in STRINGS else "en"
