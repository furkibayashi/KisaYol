from datetime import datetime

import pytest

from kisayol.clipboard import ClipboardError
from kisayol.config import DEFAULTS
from kisayol.expander import Expander
from kisayol.matcher import Match
from kisayol.snippets import Snippet


class FakeSink:
    def __init__(self, pressed=()):
        self.events = []
        self.pressed = set(pressed)

    def tap(self, key):
        self.events.append(("tap", key))

    def write(self, text, delay_ms):
        self.events.append(("write", text))

    def release(self, key):
        self.events.append(("release", key))

    def is_pressed(self, key):
        return key in self.pressed


class FakeClip:
    ClipboardError = ClipboardError

    def __init__(self, text="eski", fail_backup=False):
        self.text = text
        self.fail_backup = fail_backup
        self.log = None

    def get_text(self):
        return self.text

    def backup(self):
        if self.fail_backup:
            raise ClipboardError("kilitli")
        return [(13, b"BACKUP")]

    def set_text(self, s):
        self.log.append(("set_text", s))

    def restore(self, data):
        self.log.append(("restore", data))


class Clock:
    def __init__(self):
        self.total = 0.0

    def sleep(self, s):
        self.total += s


def make(sink=None, clip=None, **settings):
    sink = sink or FakeSink()
    clip = clip or FakeClip()
    clip.log = sink.events
    cfg = dict(DEFAULTS["app"])
    cfg.update(settings)
    clock = Clock()
    exp = Expander(sink, clip=clip, settings=cfg, sleep=clock.sleep,
                   now=lambda: datetime(2026, 11, 19, 14, 5))
    return exp, sink, clip, clock


def match(text, trigger=";adr", method="paste", delete=None, suffix=""):
    s = Snippet(trigger, text, method=method)
    return Match(s, len(trigger) if delete is None else delete, suffix)


def taps(sink, key):
    return [e for e in sink.events if e == ("tap", key)]


def test_paste_flow():
    exp, sink, _, _ = make()
    exp.expand(match("Adres"))
    assert sink.events == [("tap", "backspace")] * 4 + [
        ("set_text", "Adres"),
        ("tap", "ctrl+v"),
        ("restore", [(13, b"BACKUP")]),
    ]


def test_paste_waits_restore_delay():
    exp, _, _, clock = make(restore_delay_ms=150)
    exp.expand(match("Adres"))
    assert clock.total == pytest.approx(0.15)


def test_type_flow_uses_shift_enter():
    exp, sink, _, _ = make()
    exp.expand(match("a\nb", method="type"))
    assert sink.events[4:] == [("write", "a"), ("tap", "shift+enter"), ("write", "b")]
    assert not taps(sink, "ctrl+v")


def test_bare_suffix_rewritten():
    exp, sink, _, _ = make()
    exp.expand(match("Selamlar", trigger="slm", delete=4, suffix=","))
    assert len(taps(sink, "backspace")) == 4
    writes = [e for e in sink.events if e[0] in ("write", "set_text")]
    assert writes[-1] == ("write", ",")


def test_cursor_moves_left():
    exp, sink, _, _ = make()
    exp.expand(match("Merhaba {imleç} dünya", suffix=" "))
    assert len(taps(sink, "left")) == 7


def test_cursor_at_end_with_suffix():
    exp, sink, _, _ = make()
    exp.expand(match("son{imleç}", suffix=","))
    assert len(taps(sink, "left")) == 1


def test_no_cursor_with_suffix():
    exp, sink, _, _ = make()
    exp.expand(match("son", suffix=","))
    assert taps(sink, "left") == []


def test_waits_for_and_releases_modifiers():
    sink = FakeSink(pressed={"shift"})
    exp, sink, _, clock = make(sink=sink)
    exp.expand(match("Adres"))
    assert ("release", "shift") in sink.events
    assert sink.events.index(("release", "shift")) < sink.events.index(("tap", "backspace"))
    assert clock.total <= 0.5 + 0.15 + 1e-9


def test_paste_falls_back_to_typing_when_backup_fails():
    exp, sink, _, _ = make(clip=FakeClip(fail_backup=True))
    exp.expand(match("Adres"))
    assert not [e for e in sink.events if e[0] in ("set_text", "restore")]
    assert ("write", "Adres") in sink.events
    assert not taps(sink, "ctrl+v")


def test_pano_variable_uses_clipboard_text():
    exp, sink, _, _ = make(clip=FakeClip(text="PANO"))
    exp.expand(match("[{pano}]"))
    assert ("set_text", "[PANO]") in sink.events


def test_date_uses_configured_format():
    exp, sink, _, _ = make(date_fmt="%Y")
    exp.expand(match("{tarih}"))
    assert ("set_text", "2026") in sink.events


def test_empty_result_only_deletes():
    exp, sink, _, _ = make()
    exp.expand(match("{imleç}"))
    assert sink.events == [("tap", "backspace")] * 4


def test_waits_for_and_releases_altgr():
    sink = FakeSink(pressed={"alt gr"})
    exp, sink, _, _ = make(sink=sink)
    exp.expand(match("Adres"))
    assert ("release", "alt gr") in sink.events
    assert sink.events.index(("release", "alt gr")) < sink.events.index(("tap", "backspace"))


def test_clipboard_restored_even_if_paste_fails():
    class Boom(FakeSink):
        def tap(self, key):
            if key == "ctrl+v":
                raise RuntimeError("tus gonderilemedi")
            super().tap(key)
    exp, sink, _, _ = make(sink=Boom())
    with pytest.raises(RuntimeError):
        exp.expand(match("Adres"))
    assert ("restore", [(13, b"BACKUP")]) in sink.events


def test_negative_restore_delay_is_clamped():
    exp, sink, _, clock = make(restore_delay_ms=-5)
    exp.expand(match("Adres"))
    assert clock.total == 0
    assert ("restore", [(13, b"BACKUP")]) in sink.events
