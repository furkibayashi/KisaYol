"""Uçtan uca kontrol: kendi Tk metin penceresini açar, gerçek tuş olayları gönderir, sonucu doğrular.

Yalnızca kendi penceresi önde olduğunda tuş gönderir; değilse durur. Kullanıcının panosu korunur.
Kullanım:  py scripts/e2e_check.py   (pencere öne gelemezse ona bir kez tıklayın)
"""
import ctypes
import json
import os
import subprocess
import sys
import threading
import time
import tkinter as tk
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kisayol import clipboard  # noqa: E402
from kisayol.snippets import Snippet  # noqa: E402
from scripts.smoke import build  # noqa: E402

SEMI = "shift+,"   # Türkçe Q klavyede ; = Shift + virgül tuşu
CASES = [
    # (gönderilecek tuşlar, beklenen metin) — "shift+x" = Shift basılıyken x
    ([SEMI, "t", "a", "r", "i", "h"], datetime.now().strftime("%d.%m.%Y")),
    (["s", "l", "m", ","], "Selamlar,"),
    (["shift+p", "a", "s", "l", "m", "space"], "Paslm "),
    ([SEMI, "i", "m", "z", "a", "shift+x"], "Saygılarımla,\nX"),
    ([SEMI, "s", "a", "t", "ı", "r"], "bir\niki"),
    ([SEMI, "p", "a", "n", "o"], "<PANO>"),
]

# keyboard kütüphanesi aynı işlemin gönderdiği tuşları kancada göstermez; bu yüzden tuşlar
# ayrı bir Python işleminden gönderilir (gerçek kullanıcı girişine en yakın durum).
SENDER = """
import json, sys, time, keyboard, ctypes
u = ctypes.windll.user32
def fg():
    b = ctypes.create_unicode_buffer(128)
    u.GetWindowTextW(u.GetForegroundWindow(), b, 128)
    return b.value
def sc(name):
    return keyboard.key_to_scan_codes(name)[0]
keys = json.loads(sys.argv[1])
for i, k in enumerate(keys):
    last = i == len(keys) - 1
    hold = 0.15 if last else 0   # son tuş insan gibi basılı tutulur (genişletme bu sırada çalışır)
    if k.startswith("shift+"):
        keyboard.press("shift"); keyboard.press(sc(k[6:])); time.sleep(hold)
        keyboard.release(sc(k[6:])); keyboard.release("shift")
    else:
        keyboard.press(sc(k)); time.sleep(hold); keyboard.release(sc(k))
    time.sleep(0.05)
    if len(sys.argv) > 2: open(sys.argv[2], "a", encoding="utf-8").write(f"{k} -> {fg()}" + chr(10))
time.sleep(0.5)
if len(sys.argv) > 2: open(sys.argv[2], "a", encoding="utf-8").write(f"after -> {fg()}" + chr(10))
"""

SNIPPETS = [
    Snippet(";tarih", "{tarih}"),
    Snippet("slm", "Selamlar"),
    Snippet(";imza", "Saygılarımla,\n{imleç}"),
    Snippet(";satır", "bir\niki", method="type"),
    Snippet(";pano", "<{pano}>"),
]


TRACE = sys.argv[sys.argv.index("--trace") + 1] if "--trace" in sys.argv else ""


def send_keys(keys):
    subprocess.run([sys.executable, "-c", SENDER, json.dumps(keys)] + ([TRACE] if TRACE else []),
                   check=True, timeout=20,
                   creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))


def main():
    import faulthandler
    faulthandler.dump_traceback_later(60, exit=True)
    root = tk.Tk()
    root.title("KisaYol E2E")
    root.attributes("-topmost", True)
    info = tk.Label(root, text="Test çalışıyor, dokunmayın…")
    info.pack()
    text = tk.Text(root, width=50, height=8)
    text.pack()
    results = []
    saved = clipboard.backup()
    clipboard.set_text("PANO")

    hook, worker = build(SNIPPETS)
    hook.skip_own_windows = False   # test penceresi kancayla aynı işlemde
    hook.start()

    user32 = ctypes.windll.user32
    user32.GetForegroundWindow.restype = ctypes.c_void_p
    user32.GetParent.restype = ctypes.c_void_p
    user32.GetParent.argtypes = [ctypes.c_void_p]

    user32.SetForegroundWindow.argtypes = [ctypes.c_void_p]

    user32.GetAncestor.restype = ctypes.c_void_p
    user32.GetAncestor.argtypes = [ctypes.c_void_p, ctypes.c_uint]

    # Tk'ye yalnızca ana iş parçacığından dokunulur: tutamaç burada bir kez alınır.
    root.update()
    top = user32.GetAncestor(root.winfo_id(), 2)   # GA_ROOT

    def top_hwnd():
        return top

    def bring_to_front():
        # Windows odak kilidi: bir Alt basışı, işlemin pencereyi öne getirmesine izin verir.
        user32.keybd_event(0x12, 0, 0, 0)
        user32.keybd_event(0x12, 0, 2, 0)
        user32.SetForegroundWindow(top_hwnd())

    def ours():
        fg = user32.GetForegroundWindow()
        return fg == top_hwnd()

    def run():
        time.sleep(1.0)
        for keys, expected in CASES:
            root.after(0, lambda: (text.delete("1.0", "end"), text.focus_force()))
            for _ in range(8):
                if ours():
                    break
                root.after(0, bring_to_front)   # Alt dokunuşu yalnızca gerektiğinde (sonraki tuşu yutabilir)
                time.sleep(0.25)
            if not ours():
                root.after(0, lambda: info.config(text="Devam etmek için bu pencereye tıklayın…"))
                deadline = time.time() + 60
                while not ours() and time.time() < deadline:
                    time.sleep(0.2)
                root.after(0, lambda: (info.config(text="Test çalışıyor, dokunmayın…"), text.focus_force()))
                time.sleep(0.3)
            if not ours():
                results.append(("ABORT", "pencere önde değil", ""))
                break
            send_keys(keys)
            time.sleep(0.6)
            if not ours():
                buf = ctypes.create_unicode_buffer(256)
                user32.GetWindowTextW(ctypes.c_void_p(user32.GetForegroundWindow()), buf, 256)
                results.append(("ABORT", "odak kaçtı", repr(buf.value)))
                break
            box = {}
            root.after(0, lambda: box.setdefault("v", text.get("1.0", "end-1c")))
            time.sleep(0.2)
            got = box.get("v")
            results.append(("OK" if got == expected else "FAIL", repr(expected), repr(got)))
        time.sleep(0.5)
        clip_after = clipboard.get_text()
        results.append(("OK" if clip_after == "PANO" else "FAIL", "pano korunmuş: 'PANO'", repr(clip_after)))
        root.after(0, root.destroy)

    threading.Thread(target=run, daemon=True).start()
    root.after(200, lambda: (root.lift(), root.focus_force(), text.focus_set()))
    root.mainloop()
    hook.close()
    clipboard.restore(saved)
    for r in results:
        print(*r, sep=" | ")
    sys.exit(0 if all(r[0] == "OK" for r in results) else 1)


if __name__ == "__main__":
    main()
