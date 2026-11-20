from kisayol import i18n


def test_turkish_and_english_have_same_keys():
    assert set(i18n.STRINGS["tr"]) == set(i18n.STRINGS["en"])


def test_missing_language_key_falls_back_to_english(monkeypatch):
    monkeypatch.setitem(i18n.STRINGS, "de", {})
    i18n.set_language("de")
    assert i18n.T("nav_snippets") == i18n.STRINGS["en"]["nav_snippets"]


def test_format_args():
    i18n.set_language("tr")
    assert "3" in i18n.T("snippet_count", n=3)


def test_all_seven_languages_selectable():
    for code, _name in i18n.LANGUAGES:
        assert code in i18n.STRINGS
