"""Arayüzsüz duman testi: kalıpları yükler, kancayı başlatır, Ctrl+C ile durana kadar genişletir.

Kullanım:  py scripts/smoke.py
Sonra Not Defteri'nde ;tarih  slm,  ;imza  ;mail yazıp deneyin. (slm kalıbı bu betikte geçici olarak eklenir.)
"""
import os
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from kisayol.config import DEFAULTS  # noqa: E402
from kisayol.expander import Expander  # noqa: E402
from kisayol.hook import ExpansionWorker, KeyboardSink, KeyHook  # noqa: E402
from kisayol.matcher import Matcher  # noqa: E402
from kisayol.snippets import Snippet, SnippetStore  # noqa: E402


def build(snippets, settings=None):
    matcher = Matcher()
    matcher.set_snippets(snippets)
    hook = KeyHook(matcher, on_match=lambda m: worker.submit(m), post=lambda e: None)
    expander = Expander(KeyboardSink(), settings=settings or dict(DEFAULTS["app"]))
    worker = ExpansionWorker(hook, expander)
    return hook, worker


def main():
    store = SnippetStore(os.path.join(tempfile.mkdtemp(), "snippets.json"))
    store.load()
    store.snippets.append(Snippet("slm", "Selamlar"))
    hook, worker = build(store.active())
    hook.start()
    print("KısaYol duman testi çalışıyor:", ", ".join(s.trigger for s in store.active()))
    print("Durdurmak için Ctrl+C.")
    try:
        while True:
            time.sleep(0.5)
    except KeyboardInterrupt:
        hook.close()


if __name__ == "__main__":
    main()
