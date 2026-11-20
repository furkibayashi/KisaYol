from kisayol.hook import KeyHook, parse_combo


class FakeMatcher:
    def __init__(self, hit_on=None):
        self.calls = []
        self.hit_on = hit_on

    def feed(self, ch):
        self.calls.append(("feed", ch))
        return "MATCH" if ch == self.hit_on else None

    def backspace(self):
        self.calls.append(("backspace",))

    def reset(self):
        self.calls.append(("reset",))


def make(hit_on=None):
    m = FakeMatcher(hit_on)
    matches, posts = [], []
    hook = KeyHook(m, on_match=matches.append, post=posts.append)
    hook.set_hotkeys("ctrl+alt+p", "ctrl+alt+space")
    return hook, m, matches, posts


def test_printable_fed_with_case():
    hook, m, _, _ = make()
    hook.handle_key("A", "down", {"shift"})
    hook.handle_key("ş", "down", set())
    assert m.calls == [("feed", "A"), ("feed", "ş")]


def test_space_fed_as_character():
    hook, m, _, _ = make()
    hook.handle_key("space", "down", set())
    assert m.calls == [("feed", " ")]


def test_key_up_ignored():
    hook, m, _, _ = make()
    hook.handle_key("a", "up", set())
    assert m.calls == []


def test_match_forwarded():
    hook, _, matches, _ = make(hit_on="r")
    hook.handle_key("r", "down", set())
    assert matches == ["MATCH"]


def test_backspace_calls_matcher_backspace():
    hook, m, _, _ = make()
    hook.handle_key("backspace", "down", set())
    assert m.calls == [("backspace",)]


def test_reset_keys():
    for key in ("enter", "tab", "esc", "left", "right", "up", "down", "home", "end",
                "page up", "page down", "delete", "insert"):
        hook, m, _, _ = make()
        hook.handle_key(key, "down", set())
        assert m.calls == [("reset",)], key


def test_modifier_alone_ignored():
    hook, m, _, _ = make()
    for key in ("shift", "ctrl", "alt", "alt gr", "windows", "caps lock"):
        hook.handle_key(key, "down", set())
    assert m.calls == []


def test_ctrl_combo_resets():
    hook, m, _, _ = make()
    hook.handle_key("c", "down", {"ctrl"})
    assert m.calls == [("reset",)]


def test_alt_and_win_combos_reset():
    hook, m, _, _ = make()
    hook.handle_key("x", "down", {"alt"})
    hook.handle_key("d", "down", {"windows"})
    assert m.calls == [("reset",), ("reset",)]


def test_altgr_character_is_fed():
    hook, m, _, _ = make()
    hook.handle_key("@", "down", {"ctrl", "alt"})
    hook.handle_key("€", "down", {"ctrl", "alt gr"})
    assert m.calls == [("feed", "@"), ("feed", "€")]


def test_suspended_hook_does_not_feed_matcher():
    hook, m, _, _ = make()
    with hook.suspended():
        hook.handle_key("a", "down", set())
        hook.handle_key("backspace", "down", set())
    assert m.calls == [("reset",)]


def test_paused_ignores_typing_but_hotkeys_work():
    hook, m, _, posts = make()
    hook.paused = True
    hook.handle_key("a", "down", set())
    assert m.calls == []
    hook.handle_key("p", "down", {"ctrl", "alt"})
    assert posts == [("hotkey", "pause")]


def test_search_hotkey_posts_and_is_not_fed():
    hook, m, _, posts = make()
    hook.handle_key("space", "down", {"ctrl", "alt"})
    assert posts == [("hotkey", "search")]
    assert ("feed", " ") not in m.calls


def test_hotkey_requires_exact_modifiers():
    hook, _, _, posts = make()
    hook.handle_key("p", "down", {"ctrl", "alt", "shift"})
    assert posts == []


def test_click_resets():
    hook, m, _, _ = make()
    hook.handle_click()
    assert m.calls == [("reset",)]


def test_foreground_change_resets():
    hook, m, _, _ = make()
    hook.on_foreground_change()
    assert m.calls == [("reset",)]


def test_parse_combo():
    assert parse_combo("ctrl+alt+space") == (frozenset({"ctrl", "alt"}), "space")
    assert parse_combo("") is None
