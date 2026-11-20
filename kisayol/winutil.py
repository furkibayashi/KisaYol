"""Windows'a özgü yardımcılar: tek örnek, yönetici yetkisi, otomatik başlatma, pencereyi öne getirme."""
from __future__ import annotations

import ctypes
import os
import sys
from ctypes import wintypes

from . import APP_ID

IS_WIN = sys.platform == "win32"
RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"

if IS_WIN:
    _u = ctypes.WinDLL("user32", use_last_error=True)
    _k = ctypes.WinDLL("kernel32", use_last_error=True)
    _u.GetForegroundWindow.restype = wintypes.HWND
    _u.SetForegroundWindow.argtypes = [wintypes.HWND]
    _u.GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
    _u.GetWindowThreadProcessId.restype = wintypes.DWORD
    _u.AttachThreadInput.argtypes = [wintypes.DWORD, wintypes.DWORD, wintypes.BOOL]
    _u.BringWindowToTop.argtypes = [wintypes.HWND]
    _u.GetAncestor.argtypes = [wintypes.HWND, wintypes.UINT]
    _u.GetAncestor.restype = wintypes.HWND
    _k.CreateMutexW.restype = wintypes.HANDLE
    _k.CreateEventW.restype = wintypes.HANDLE
    _k.OpenEventW.restype = wintypes.HANDLE
    _k.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    _k.SetEvent.argtypes = [wintypes.HANDLE]
    _k.CloseHandle.argtypes = [wintypes.HANDLE]


def foreground_window():
    return _u.GetForegroundWindow() if IS_WIN else None


def root_hwnd(widget_id: int):
    """Tk winfo_id() → üst düzey pencere tutamacı."""
    return _u.GetAncestor(widget_id, 2) if IS_WIN else None


class _RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long), ("right", ctypes.c_long), ("bottom", ctypes.c_long)]


class _MONITORINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("rcMonitor", _RECT), ("rcWork", _RECT), ("dwFlags", wintypes.DWORD)]


def work_area_at(x: int, y: int):
    """(sol, üst, sağ, alt): verilen noktanın bulunduğu ekranın görev çubuğu hariç alanı."""
    if not IS_WIN:
        return None
    try:
        _u.MonitorFromPoint.argtypes = [wintypes.POINT, wintypes.DWORD]
        _u.MonitorFromPoint.restype = wintypes.HMONITOR
        _u.GetMonitorInfoW.argtypes = [wintypes.HMONITOR, ctypes.POINTER(_MONITORINFO)]
        mon = _u.MonitorFromPoint(wintypes.POINT(x, y), 2)   # MONITOR_DEFAULTTONEAREST
        info = _MONITORINFO()
        info.cbSize = ctypes.sizeof(_MONITORINFO)
        if _u.GetMonitorInfoW(mon, ctypes.byref(info)):
            r = info.rcWork
            return r.left, r.top, r.right, r.bottom
    except Exception:
        pass
    return None


def force_foreground(hwnd) -> None:
    """Odak kilidine takılmadan pencereyi öne getirir (giriş kuyruğunu geçici olarak bağlayarak)."""
    if not IS_WIN or not hwnd:
        return
    # Odak kilidi "son girdi olayını alan işlem" kuralına bakar: zararsız bir boş tuş olayı (VK 0) bizi o işlem yapar.
    # (Alt kullanılmaz: hedef uygulamada menü çubuğunu etkinleştirir.)
    _u.keybd_event(0, 0, 0, 0)
    _u.keybd_event(0, 0, 2, 0)
    fg = _u.GetForegroundWindow()
    cur = _k.GetCurrentThreadId()
    other = _u.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = bool(other and other != cur and _u.AttachThreadInput(other, cur, True))
    try:
        _u.BringWindowToTop(hwnd)
        _u.SetForegroundWindow(hwnd)
    finally:
        if attached:
            _u.AttachThreadInput(other, cur, False)


class _GUITHREADINFO(ctypes.Structure):
    _fields_ = [("cbSize", wintypes.DWORD), ("flags", wintypes.DWORD), ("hwndActive", wintypes.HWND),
                ("hwndFocus", wintypes.HWND), ("hwndCapture", wintypes.HWND), ("hwndMenuOwner", wintypes.HWND),
                ("hwndMoveSize", wintypes.HWND), ("hwndCaret", wintypes.HWND), ("rcCaret", _RECT)]


def capture_focus():
    """(üst pencere, klavye odağındaki iç denetim) — arama penceresi açılmadan önce kaydedilir."""
    if not IS_WIN:
        return None, None
    top = _u.GetForegroundWindow()
    if not top:
        return None, None
    info = _GUITHREADINFO()
    info.cbSize = ctypes.sizeof(_GUITHREADINFO)
    tid = _u.GetWindowThreadProcessId(top, None)
    try:
        _u.GetGUIThreadInfo.argtypes = [wintypes.DWORD, ctypes.POINTER(_GUITHREADINFO)]
        if _u.GetGUIThreadInfo(tid, ctypes.byref(info)):
            return top, info.hwndFocus
    except Exception:
        pass
    return top, None


def restore_focus(top, focus) -> None:
    """Üst pencereyi öne getirir ve klavye odağını önceki iç denetime geri verir.

    Modern (XAML) uygulamalar, örn. Windows 11 Not Defteri, yalnızca öne getirildiğinde metin alanına
    odağı geri vermez; SetFocus o pencerenin iş parçacığına bağlanarak yapılmalıdır.
    """
    if not IS_WIN or not top:
        return
    force_foreground(top)
    if not focus:
        return
    cur = _k.GetCurrentThreadId()
    other = _u.GetWindowThreadProcessId(focus, None)
    attached = bool(other and other != cur and _u.AttachThreadInput(cur, other, True))
    try:
        _u.SetFocus.argtypes = [wintypes.HWND]
        _u.SetFocus(focus)
    finally:
        if attached:
            _u.AttachThreadInput(cur, other, False)


class SingleInstance:
    """Aynı anda iki KısaYol çalışırsa her tetikleyici iki kez genişler; bunu engeller."""

    def __init__(self):
        self._mutex = None
        self._event = None

    def acquire(self) -> bool:
        if not IS_WIN:
            return True
        self._mutex = _k.CreateMutexW(None, False, f"Local\\{APP_ID}_SingleInstance")
        if ctypes.get_last_error() == 183 or _k.GetLastError() == 183:   # ERROR_ALREADY_EXISTS
            _k.CloseHandle(self._mutex)
            self._mutex = None
            return False
        self._event = _k.CreateEventW(None, False, False, f"Local\\{APP_ID}_Show")
        return True

    @staticmethod
    def signal_show() -> None:
        """Çalışan örneğe 'pencereni göster' der."""
        if not IS_WIN:
            return
        h = _k.OpenEventW(0x0002, False, f"Local\\{APP_ID}_Show")   # EVENT_MODIFY_STATE
        if h:
            _k.SetEvent(h)
            _k.CloseHandle(h)

    def show_requested(self) -> bool:
        return bool(self._event) and _k.WaitForSingleObject(self._event, 0) == 0

    def release(self) -> None:
        for h in (self._event, self._mutex):
            if h:
                _k.CloseHandle(h)
        self._event = self._mutex = None


def is_admin() -> bool:
    if not IS_WIN:
        return False
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def relaunch_as_admin() -> bool:
    """Uygulamayı yönetici olarak yeniden başlatır (UAC penceresi açılır)."""
    if not IS_WIN:
        return False
    if getattr(sys, "frozen", False):
        exe, params, cwd = sys.executable, "--elevated", os.path.dirname(sys.executable)
    else:
        exe = sys.executable
        if exe.lower().endswith("python.exe"):
            pyw = exe[:-10] + "pythonw.exe"
            exe = pyw if os.path.exists(pyw) else exe
        cwd = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        params = "-m kisayol --elevated"
    return ctypes.windll.shell32.ShellExecuteW(None, "runas", exe, params, cwd, 1) > 32


def autostart_supported() -> bool:
    return IS_WIN and getattr(sys, "frozen", False)


def autostart_enabled() -> bool:
    if not IS_WIN:
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as k:
            winreg.QueryValueEx(k, APP_ID)
            return True
    except OSError:
        return False


def set_autostart(enabled: bool) -> bool:
    """Yalnızca exe sürümünde; HKCU\\...\\Run altına '"exe" --tray' yazar ya da siler."""
    if not autostart_supported():
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as k:
            if enabled:
                winreg.SetValueEx(k, APP_ID, 0, winreg.REG_SZ, f'"{sys.executable}" --tray')
            else:
                try:
                    winreg.DeleteValue(k, APP_ID)
                except FileNotFoundError:
                    pass
        return True
    except OSError:
        return False
