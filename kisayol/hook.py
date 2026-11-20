"""Klavye/fare kancası: tuşları eşleştiriciye besler, kısayolları bildirir, genişletmeyi işçi iş parçacığında yapar.

Gizlilik: yazılan karakterler yalnızca Matcher'ın bellekteki (en çok 64 karakterlik) tamponuna gider.
Bu modül hiçbir şeyi diske yazmaz, loglamaz, ağa göndermez.
"""
from __future__ import annotations

import contextlib
import queue
import sys
import threading
import time
from typing import Callable, Optional, Set

MODIFIERS = {"ctrl", "shift", "alt", "alt gr", "windows"}
LOCK_KEYS = {"caps lock", "num lock", "scroll lock"}
RESET_KEYS = {"enter", "tab", "esc", "left", "right", "up", "down", "home", "end",
              "page up", "page down", "delete", "insert"}
SETTLE_SECONDS = 0.03        # kendi enjekte ettiğimiz tuşların kancadan geçmesi için
FOREGROUND_POLL = 0.25


def normalize_key(name):
    """OtoTık engine.normalize_key."""
    if not name:
        return ""
    n = name.lower()
    for pre in ("left ", "right "):
        if n.startswith(pre) and n[len(pre):] in ("ctrl", "shift", "alt", "windows"):
            n = n[len(pre):]
    return {"control": "ctrl", "win": "windows", "cmd": "windows", "escape": "esc",
            "return": "enter", "spacebar": "space"}.get(n, n)


def parse_combo(combo):
    """"ctrl+f8" -> (frozenset({'ctrl'}), 'f8'). OtoTık engine.parse_combo."""
    combo = (combo or "").strip().lower()
    if not combo:
        return None
    parts = [normalize_key(p.strip()) for p in combo.split("+") if p.strip()]
    if not parts:
        return None
    return frozenset(parts[:-1]), parts[-1]


def pretty_combo(combo):
    if not combo:
        return "—"
    return " + ".join(p.strip().upper() if len(p.strip()) <= 3 else p.strip().title() for p in combo.split("+"))


class KeyHook:
    def __init__(self, matcher, on_match: Callable, post: Callable[[tuple], None]):
        self.matcher = matcher
        self.on_match = on_match
        self.post = post
        self.paused = False
        self._suspended = 0
        self._hotkeys = {}
        self._pressed: Set[str] = set()
        self._started = False
        self._stop = threading.Event()
        self._capture_cb: Optional[Callable] = None

    # --- yapılandırma ---
    def set_hotkeys(self, pause: str, search: str) -> None:
        hk = {}
        for action, combo in (("pause", pause), ("search", search)):
            parsed = parse_combo(combo)
            if parsed:
                hk[action] = parsed
        self._hotkeys = hk

    def start_capture(self, callback: Callable) -> None:
        """Sonraki tuş kombinasyonunu callback("ctrl+alt+k") ile verir; Esc → callback(None)."""
        self._capture_cb = callback

    def cancel_capture(self) -> None:
        self._capture_cb = None

    @contextlib.contextmanager
    def suspended(self):
        self._suspended += 1
        try:
            yield
        finally:
            self._suspended -= 1
            if not self._suspended:
                self.matcher.reset()

    # --- çekirdek (test edilebilir) ---
    def handle_key(self, name: str, event_type: str, pressed: Set[str]) -> None:
        if self._suspended or event_type != "down" or not name:
            return
        key = normalize_key(name)
        if key in MODIFIERS or key in LOCK_KEYS:
            return
        held = {m for m in pressed if m in MODIFIERS}

        if self._capture_cb is not None:
            cb, self._capture_cb = self._capture_cb, None
            cb(None if key == "esc" else "+".join(sorted(held - {"alt gr"}) + [key]))
            return

        for action, (mods, hk_key) in self._hotkeys.items():
            if hk_key == key and set(mods) == held:
                self.post(("hotkey", action))
                return
        if self.paused:
            return

        if key == "backspace":
            self.matcher.backspace()
            return
        if key in RESET_KEYS:
            self.matcher.reset()
            return

        ch = " " if key == "space" else (name if len(name) == 1 else None)
        altgr = "alt gr" in held or {"ctrl", "alt"} <= held
        if held & {"ctrl", "alt", "windows"} and not (altgr and ch is not None):
            self.matcher.reset()
            return
        if ch is None:
            return                     # F tuşları vb.: tamponu etkilemez
        m = self.matcher.feed(ch)
        if m is not None:
            self.on_match(m)

    def handle_click(self) -> None:
        if not self._suspended:
            self.matcher.reset()

    def on_foreground_change(self) -> None:
        self.matcher.reset()

    # --- gerçek kancalar ---
    def start(self) -> None:
        import keyboard
        import mouse
        if self._started:
            return
        self._started = True
        keyboard.hook(self._on_key)
        mouse.hook(self._on_mouse)
        threading.Thread(target=self._poll_foreground, daemon=True).start()

    def close(self) -> None:
        self._stop.set()
        if not self._started:
            return
        try:
            import keyboard
            keyboard.unhook_all()
        except Exception:
            pass
        try:
            import mouse
            mouse.unhook_all()
        except Exception:
            pass

    def _on_key(self, e) -> None:
        try:
            key = normalize_key(e.name or "")
            if key in MODIFIERS:
                if e.event_type == "down":
                    self._pressed.add(key)
                else:
                    self._pressed.discard(key)
            self.handle_key(e.name or "", e.event_type, set(self._pressed))
        except Exception:
            pass

    def _on_mouse(self, e) -> None:
        try:
            import mouse
            if isinstance(e, mouse.ButtonEvent) and e.event_type in ("down", "double"):
                self.handle_click()
        except Exception:
            pass

    def _poll_foreground(self) -> None:
        if sys.platform != "win32":
            return
        import ctypes
        get = ctypes.windll.user32.GetForegroundWindow
        get.restype = ctypes.c_void_p
        last = get()
        while not self._stop.wait(FOREGROUND_POLL):
            cur = get()
            if cur != last:
                last = cur
                self.on_foreground_change()


class ExpansionWorker:
    """Genişletmeleri kanca iş parçacığının dışında, sırayla yapar."""

    def __init__(self, hook: KeyHook, expander, on_done: Optional[Callable] = None):
        self.hook = hook
        self.expander = expander
        self.on_done = on_done
        self._q: "queue.Queue" = queue.Queue()
        threading.Thread(target=self._run, daemon=True).start()

    def submit(self, match) -> None:
        self._q.put(match)

    def _run(self) -> None:
        while True:
            m = self._q.get()
            if m is None:
                return
            try:
                with self.hook.suspended():
                    self.expander.expand(m)
                    time.sleep(SETTLE_SECONDS)
                if self.on_done:
                    self.on_done(m)
            except Exception:
                pass

    def stop(self) -> None:
        self._q.put(None)


class KeyboardSink:
    """KeySink'in `keyboard` kütüphanesiyle gerçek uygulaması."""

    def tap(self, key: str) -> None:
        import keyboard
        keyboard.send(key)

    def write(self, text: str, delay_ms: int) -> None:
        import keyboard
        keyboard.write(text, delay=max(0, delay_ms) / 1000.0)

    def release(self, key: str) -> None:
        import keyboard
        try:
            keyboard.release(key)
        except Exception:
            pass

    def is_pressed(self, key: str) -> bool:
        import keyboard
        try:
            return keyboard.is_pressed(key)
        except Exception:
            return False
