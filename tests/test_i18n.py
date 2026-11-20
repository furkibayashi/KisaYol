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


def test_every_language_translates_every_key():
    en = set(i18n.STRINGS["en"])
    for code, _name in i18n.LANGUAGES:
        missing = en - set(i18n.STRINGS[code])
        assert not missing, (code, sorted(missing))


def test_error_keys_exist_for_validation():
    for key in ("err_empty", "err_short", "err_space", "err_bare_not_alnum", "err_duplicate", "err_prefix_conflict"):
        assert key in i18n.STRINGS["en"]
