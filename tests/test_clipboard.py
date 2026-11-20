import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows panosu gerekir")


@pytest.fixture
def clip():
    from kisayol import clipboard
    saved = clipboard.backup()
    yield clipboard
    clipboard.restore(saved)


def test_unicode_roundtrip(clip):
    clip.set_text("İğ✓ şık\nyeni satır")
    assert clip.get_text() == "İğ✓ şık\nyeni satır"


def test_backup_restore_text(clip):
    clip.set_text("a")
    data = clip.backup()
    clip.set_text("z")
    clip.restore(data)
    assert clip.get_text() == "a"


def test_backup_restore_keeps_html_format(clip):
    import ctypes
    fmt = ctypes.windll.user32.RegisterClipboardFormatW("HTML Format")
    html = b"Version:0.9\r\n<b>kalin</b>\x00"
    clip.restore([(13, "düz\x00".encode("utf-16-le")), (fmt, html)])
    data = clip.backup()
    clip.set_text("z")
    clip.restore(data)
    formats = dict(clip.backup())
    assert clip.get_text() == "düz"
    assert formats[fmt].rstrip(b"\x00") == html.rstrip(b"\x00")


def test_empty_restore_clears(clip):
    clip.set_text("x")
    clip.restore([])
    assert clip.get_text() == ""
