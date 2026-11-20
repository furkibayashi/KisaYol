import json

from kisayol.snippets import (
    DEFAULT_SNIPPETS,
    Snippet,
    SnippetStore,
    is_symbol_trigger,
    validate_trigger,
)


def test_symbol_detection():
    assert is_symbol_trigger(";adr") is True
    assert is_symbol_trigger("slm") is False
    assert is_symbol_trigger("/imza") is True


def test_validation_rules():
    adr = Snippet(";adr", "Adres")
    assert validate_trigger("", []) == "err_empty"
    assert validate_trigger(";", []) == "err_short"
    assert validate_trigger("; a", []) == "err_space"
    assert validate_trigger(";a\nb", []) == "err_space"
    assert validate_trigger("sl.m", []) == "err_bare_not_alnum"
    assert validate_trigger(";adr", [adr]) == "err_duplicate"
    assert validate_trigger(";adr", [adr], self_id=adr.id) is None


def test_duplicate_checked_against_disabled_too():
    off = Snippet(";adr", "Adres", enabled=False)
    assert validate_trigger(";adr", [off]) == "err_duplicate"


def test_prefix_conflict_both_directions():
    assert validate_trigger(";a", [Snippet(";ad", "x")]) == "err_prefix_conflict"
    assert validate_trigger(";ad", [Snippet(";a", "x")]) == "err_prefix_conflict"
    assert validate_trigger(";ad", [Snippet(";a", "x", enabled=False)]) is None


def test_bare_prefix_pair_allowed():
    assert validate_trigger("slm", [Snippet("sl", "x")]) is None


def test_save_load_roundtrip(tmp_path):
    path = tmp_path / "snippets.json"
    store = SnippetStore(str(path))
    store.load()
    store.snippets = []
    store.add(Snippet(";tr", "İğüşöç\nı", group="Türkçe"))
    store.save()

    again = SnippetStore(str(path))
    again.load()
    assert [(s.trigger, s.text, s.group) for s in again.snippets] == [(";tr", "İğüşöç\nı", "Türkçe")]
    assert "Türkçe" in again.groups and "Genel" in again.groups
    assert "İ" in path.read_text("utf-8")


def test_missing_file_creates_defaults(tmp_path):
    store = SnippetStore(str(tmp_path / "snippets.json"))
    store.load()
    assert [s.trigger for s in store.snippets] == [s.trigger for s in DEFAULT_SNIPPETS]
    assert [s.trigger for s in store.snippets] == [";tarih", ";mail", ";imza"]


def test_defaults_are_fresh_copies(tmp_path):
    store = SnippetStore(str(tmp_path / "snippets.json"))
    store.load()
    store.snippets[0].text = "changed"
    assert DEFAULT_SNIPPETS[0].text == "{tarih}"


def test_corrupt_file_is_backed_up(tmp_path):
    path = tmp_path / "snippets.json"
    path.write_text("{bozuk", encoding="utf-8")
    store = SnippetStore(str(path))
    store.load()
    bak = tmp_path / "snippets.json.bak"
    assert bak.read_text("utf-8") == "{bozuk"
    assert [s.trigger for s in store.snippets] == [s.trigger for s in DEFAULT_SNIPPETS]


def test_invalid_entries_skipped(tmp_path):
    path = tmp_path / "snippets.json"
    path.write_text(json.dumps({
        "version": 1,
        "groups": ["Genel"],
        "snippets": [
            {"text": "trigger yok"},
            {"trigger": ";a", "text": "A"},
            {"trigger": ";ad", "text": "AD"},
            "metin",
        ],
    }), encoding="utf-8")
    store = SnippetStore(str(path))
    store.load()
    assert [(s.trigger, s.enabled) for s in store.snippets] == [(";a", True), (";ad", False)]


def test_unknown_method_falls_back_to_paste(tmp_path):
    path = tmp_path / "snippets.json"
    path.write_text(json.dumps({"snippets": [{"trigger": ";x", "text": "X", "method": "fax"}]}),
                    encoding="utf-8")
    store = SnippetStore(str(path))
    store.load()
    assert store.snippets[0].method == "paste"


def test_import_disables_conflicts(tmp_path):
    store = SnippetStore(str(tmp_path / "snippets.json"))
    store.load()
    store.snippets = [Snippet(";a", "A")]
    src = tmp_path / "import.json"
    src.write_text(json.dumps({"snippets": [{"trigger": ";ad", "text": "AD"}]}), encoding="utf-8")
    assert store.import_from(str(src)) == [";ad"]
    imported = [s for s in store.snippets if s.trigger == ";ad"][0]
    assert imported.enabled is False


def test_import_skips_existing_trigger(tmp_path):
    store = SnippetStore(str(tmp_path / "snippets.json"))
    store.load()
    store.snippets = [Snippet(";a", "eski")]
    src = tmp_path / "import.json"
    src.write_text(json.dumps({"snippets": [{"trigger": ";a", "text": "yeni"}]}), encoding="utf-8")
    assert store.import_from(str(src)) == [";a"]
    assert [(s.trigger, s.text) for s in store.snippets] == [(";a", "eski")]


def test_export_import_roundtrip(tmp_path):
    a = SnippetStore(str(tmp_path / "a.json"))
    a.load()
    a.export_to(str(tmp_path / "out.json"))
    b = SnippetStore(str(tmp_path / "b.json"))
    b.load()
    b.snippets = []
    assert b.import_from(str(tmp_path / "out.json")) == []
    assert [s.trigger for s in b.snippets] == [";tarih", ";mail", ";imza"]


def test_on_change_called_on_mutation(tmp_path):
    store = SnippetStore(str(tmp_path / "s.json"))
    store.load()
    calls = []
    store.on_change = lambda: calls.append(1)
    s = Snippet(";n", "N")
    store.add(s)
    s.text = "M"
    store.update(s)
    store.remove(s.id)
    assert len(calls) == 3
    assert all(x.id != s.id for x in store.snippets)


def test_active_excludes_disabled(tmp_path):
    store = SnippetStore(str(tmp_path / "s.json"))
    store.load()
    store.snippets = [Snippet(";a", "A"), Snippet(";b", "B", enabled=False)]
    assert [s.trigger for s in store.active()] == [";a"]
