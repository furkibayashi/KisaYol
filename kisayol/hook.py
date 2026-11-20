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
TAP_HOLD = 0.02             # kombinasyonlarda değiştiricinin basılı tutulma süresi (sn)


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


MOD_ALT, MOD_CONTROL, MOD_SHIFT, MOD_WIN, MOD_NOREPEAT = 0x0001, 0x0002, 0x0004, 0x0008, 0x4000
_MOD_BITS = {"alt": MOD_ALT, "ctrl": MOD_CONTROL, "shift": MOD_SHIFT, "windows": MOD_WIN}
_NAMED_VK = {"space": 0x20, "enter": 0x0D, "tab": 0x09, "esc": 0x1B, "backspace": 0x08, "insert": 0x2D,
             "delete": 0x2E, "home": 0x24, "end": 0x23, "page up": 0x21, "page down": 0x22, "left": 0x25,
             "up": 0x26, "right": 0x27, "down": 0x28, "pause": 0x13, "print screen": 0x2C}


def to_win_hotkey(combo: str):
    """"ctrl+alt+space" → (RegisterHotKey değiştiricileri, sanal tuş kodu); eşlenemezse None."""
    parsed = parse_combo(combo)
    if not parsed:
        return None
    mods, key = parsed
    if any(m not in _MOD_BITS for m in mods):
        return None
    bits = MOD_NOREPEAT
    for m in mods:
        bits |= _MOD_BITS[m]
    if len(key) == 1 and key.isascii() and key.isalnum():
        vk = ord(key.upper())
    elif key in _NAMED_VK:
        vk = _NAMED_VK[key]
    elif key.startswith("f") and key[1:].isdigit() and 1 <= int(key[1:]) <= 24:
        vk = 0x6F + int(key[1:])
    elif len(key) == 1 and sys.platform == "win32":
        import ctypes
        r = ctypes.windll.user32.VkKeyScanW(ord(key))
        if r == -1 or r & 0xFF == 0xFF:
            return None
        vk = r & 0xFF
    else:
        return None
    return bits, vk


class WinHotkeys:
    """RegisterHotKey ile genel kısayollar: Windows tuşu hedef uygulamaya iletmez ve bize öne gelme izni verir.

    RegisterHotKey, kaydı yapan iş parçacığının mesaj kuyruğuna WM_HOTKEY gönderir; bu yüzden kendi
    iş parçacığı ve mesaj döngüsü vardır. Kayıt değişiklikleri o iş parçacığına mesajla iletilir.
    """
    WM_HOTKEY, WM_QUIT, WM_REREGISTER = 0x0312, 0x0012, 0x8001

    def __init__(self, post):
        import ctypes
        from ctypes import wintypes
        self._ct, self._wt = ctypes, wintypes
        self._u = ctypes.WinDLL("user32", use_last_error=True)
        self._u.RegisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int, wintypes.UINT, wintypes.UINT]
        self._u.UnregisterHotKey.argtypes = [wintypes.HWND, ctypes.c_int]
        self._u.PostThreadMessageW.argtypes = [wintypes.DWORD, wintypes.UINT, wintypes.WPARAM, wintypes.LPARAM]
        self.post = post
        self._ids = {}
        self._pending = {}
        self._result = set()
        self._ready = threading.Event()
        self._done = threading.Event()
        self._tid = 0
        threading.Thread(target=self._run, daemon=True).start()
        self._ready.wait(2.0)

    def _run(self):
        ct, wt, u = self._ct, self._wt, self._u
        self._tid = ct.windll.kernel32.GetCurrentThreadId()
        msg = wt.MSG()
        u.PeekMessageW(ct.byref(msg), None, 0, 0, 0)   # mesaj kuyruğunu oluştur
        self._ready.set()
        while u.GetMessageW(ct.byref(msg), None, 0, 0) > 0:
            if msg.message == self.WM_HOTKEY:
                action = self._ids.get(msg.wParam)
                if action:
                    self.post(("hotkey", action))
            elif msg.message == self.WM_REREGISTER:
                self._reregister()
        for hid in list(self._ids):
            u.UnregisterHotKey(None, hid)

    def _reregister(self):
        for hid in list(self._ids):
            self._u.UnregisterHotKey(None, hid)
        self._ids = {}
        ok = set()
        for n, (action, combo) in enumerate(self._pending.items(), start=1):
            wh = to_win_hotkey(combo)
            if wh and self._u.RegisterHotKey(None, n, wh[0], wh[1]):
                self._ids[n] = action
                ok.add(action)
        self._result = ok
        self._done.set()

    def register(self, combos: dict) -> Set[str]:
        """{eylem: kombinasyon} kaydeder; başarıyla kaydedilen eylemleri döner (diğerleri kancadan çalışır)."""
        if not self._tid:
            return set()
        self._pending = combos
        self._done.clear()
        self._u.PostThreadMessageW(self._tid, self.WM_REREGISTER, 0, 0)
        self._done.wait(1.0)
        return set(self._result)

    def stop(self):
        if self._tid:
            self._u.PostThreadMessageW(self._tid, self.WM_QUIT, 0, 0)


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
        self._combos = {}
        self._win = None                       # WinHotkeys (gerçek kancada)
        self.external_hotkeys: Set[str] = set()  # Windows'a kaydedilen (RegisterHotKey) eylemler

    # --- yapılandırma ---
    def set_hotkeys(self, pause: str, search: str) -> None:
        hk = {}
        self._combos = {}
        for action, combo in (("pause", pause), ("search", search)):
            parsed = parse_combo(combo)
            if parsed:
                hk[action] = parsed
                self._combos[action] = combo
        self._hotkeys = hk
        if self._win is not None:
            # Windows'a kaydedilen kısayolları hedef uygulama hiç görmez; eylemi WM_HOTKEY tetikler.
            self.external_hotkeys = self._win.register(dict(self._combos))

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
                if action not in self.external_hotkeys:
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
        if sys.platform == "win32":
            self._win = WinHotkeys(self.post)
            self.external_hotkeys = self._win.register(dict(self._combos))
        mouse.hook(self._on_mouse)
        threading.Thread(target=self._poll_foreground, daemon=True).start()

    def close(self) -> None:
        self._stop.set()
        if self._win is not None:
            self._win.stop()
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
        """Kombinasyonlarda değiştiricileri kısa süre basılı tutar.

        keyboard.send her şeyi aynı anda basıp bırakır; Windows 11 Not Defteri gibi uygulamalar tuşu
        işlerken Ctrl'ü çoktan bırakılmış görür ve Ctrl+V yerine "v" yazar.
        """
        import keyboard
        parts = [p.strip() for p in key.split("+") if p.strip()]
        if len(parts) == 1:
            keyboard.send(parts[0])
            return
        mods, last = parts[:-1], parts[-1]
        for m in mods:
            keyboard.press(m)
        time.sleep(TAP_HOLD)
        keyboard.press(last)
        time.sleep(TAP_HOLD)
        keyboard.release(last)
        for m in reversed(mods):
            keyboard.release(m)

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
