import json

from kisayol.config import DEFAULTS, Config


def test_defaults(tmp_path):
    c = Config(str(tmp_path / "settings.json"))
    assert c.get("app", "pause_hotkey") == "ctrl+alt+p"
    assert c.get("app", "search_hotkey") == "ctrl+alt+space"
    assert c.get("app", "date_fmt") == "%d.%m.%Y"
    assert c.get("app", "time_fmt") == "%H:%M"
    assert c.get("app", "restore_delay_ms") == 150
    assert c["stats"]["expansions"] == 0
    assert c.first_run is True


def test_wrong_type_and_unknown_key_ignored(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"app": {"type_delay_ms": "abc", "theme": "ocean", "nope": 1}}), encoding="utf-8")
    c = Config(str(p))
    assert c.get("app", "type_delay_ms") == 2
    assert c.get("app", "theme") == "ocean"
    assert "nope" not in c["app"]
    assert c.first_run is False


def test_corrupt_json_gives_defaults(tmp_path):
    p = tmp_path / "settings.json"
    p.write_text("{bozuk", encoding="utf-8")
    c = Config(str(p))
    assert c["app"] == DEFAULTS["app"]


def test_roundtrip(tmp_path):
    p = tmp_path / "settings.json"
    c = Config(str(p))
    c["app"]["language"] = "tr"
    c["stats"]["expansions"] = 7
    c.save()
    again = Config(str(p))
    assert again.get("app", "language") == "tr"
    assert again["stats"]["expansions"] == 7


def test_defaults_not_mutated(tmp_path):
    c = Config(str(tmp_path / "settings.json"))
    c["app"]["theme"] = "neon"
    assert DEFAULTS["app"]["theme"] == "midnight"
