from datetime import datetime

from kisayol.variables import resolve

NOW = datetime(2026, 11, 19, 14, 5, 9)


def test_date_default_and_english_alias():
    assert resolve("{tarih}", NOW, "") == ("19.11.2026", None)
    assert resolve("{date}", NOW, "") == ("19.11.2026", None)


def test_time_default_and_alias():
    assert resolve("{saat}", NOW, "") == ("14:05", None)
    assert resolve("{time}", NOW, "") == ("14:05", None)


def test_custom_formats():
    assert resolve("{saat:%H:%M:%S}", NOW, "") == ("14:05:09", None)
    assert resolve("{tarih:%Y-%m-%d}", NOW, "") == ("2026-11-19", None)


def test_configured_default_formats():
    assert resolve("{tarih} {saat}", NOW, "", date_fmt="%Y/%m/%d", time_fmt="%H.%M") == ("2026/11/19 14.05", None)


def test_clipboard():
    assert resolve("A{pano}B", NOW, "x") == ("AxB", None)
    assert resolve("A{clipboard}B", NOW, "x") == ("AxB", None)


def test_clipboard_content_not_re_expanded():
    assert resolve("{pano}", NOW, "{tarih}") == ("{tarih}", None)


def test_cursor_middle():
    assert resolve("Merhaba {imleç} dünya", NOW, "") == ("Merhaba  dünya", 6)
    assert resolve("Merhaba {cursor} dünya", NOW, "") == ("Merhaba  dünya", 6)


def test_cursor_at_end_is_zero_not_none():
    assert resolve("son{imleç}", NOW, "") == ("son", 0)


def test_only_first_cursor_used():
    assert resolve("a{imleç}b{imleç}c", NOW, "") == ("abc", 2)


def test_cursor_counts_expanded_text_after_it():
    assert resolve("{imleç}{pano}", NOW, "xyz") == ("xyz", 3)


def test_escapes_and_unknown():
    assert resolve("{{tarih}}", NOW, "") == ("{tarih}", None)
    assert resolve("{bilinmeyen}", NOW, "") == ("{bilinmeyen}", None)
    assert resolve("tek { parantez", NOW, "") == ("tek { parantez", None)
    assert resolve("kapanmayan {tarih", NOW, "") == ("kapanmayan {tarih", None)


def test_invalid_format_does_not_raise():
    text, cur = resolve("{tarih:%Q}", NOW, "")
    assert isinstance(text, str) and cur is None


def test_crlf_normalized():
    assert resolve("a\r\nb", NOW, "") == ("a\nb", None)
