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


def test_capture_returns_combo_and_skips_matcher():
    hook, m, _, posts = make()
    got = []
    hook.start_capture(got.append)
    hook.handle_key("ctrl", "down", {"ctrl"})
    hook.handle_key("k", "down", {"ctrl", "alt"})
    assert got == ["alt+ctrl+k"]
    assert m.calls == [] and posts == []
    hook.handle_key("a", "down", set())
    assert m.calls == [("feed", "a")]


def test_capture_escape_cancels():
    hook, _, _, _ = make()
    got = []
    hook.start_capture(got.append)
    hook.handle_key("esc", "down", set())
    assert got == [None]



def test_external_hotkeys_not_posted_and_not_fed():
    hook, m, _, posts = make()
    hook.external_hotkeys = {"pause"}
    hook.handle_key("p", "down", {"ctrl", "alt"})
    assert posts == [] and m.calls == []
    hook.handle_key("space", "down", {"ctrl", "alt"})
    assert posts == [("hotkey", "search")]


def test_win_hotkey_mapping():
    from kisayol.hook import MOD_NOREPEAT, to_win_hotkey
    assert to_win_hotkey("ctrl+alt+space") == (0x0001 | 0x0002 | MOD_NOREPEAT, 0x20)
    assert to_win_hotkey("ctrl+alt+p") == (0x0001 | 0x0002 | MOD_NOREPEAT, ord("P"))
    assert to_win_hotkey("shift+windows+f9") == (0x0004 | 0x0008 | MOD_NOREPEAT, 0x78)
    assert to_win_hotkey("ctrl+7") == (0x0002 | MOD_NOREPEAT, ord("7"))
    assert to_win_hotkey("") is None


def test_keyboard_sink_tap_holds_modifiers(monkeypatch):
    import keyboard

    from kisayol import hook as hook_mod
    events = []
    monkeypatch.setattr(keyboard, "press", lambda k: events.append(("press", k)))
    monkeypatch.setattr(keyboard, "release", lambda k: events.append(("release", k)))
    monkeypatch.setattr(hook_mod.time, "sleep", lambda s: events.append(("sleep", s)))
    hook_mod.KeyboardSink().tap("ctrl+v")
    assert events == [("press", "ctrl"), ("sleep", hook_mod.TAP_HOLD), ("press", "v"), ("sleep", hook_mod.TAP_HOLD),
                      ("release", "v"), ("release", "ctrl")]
    assert hook_mod.TAP_HOLD >= 0.01


# --- son gözden geçirme düzeltmeleri ---

def test_unicode_units_handles_surrogates():
    from kisayol.hook import unicode_units
    assert unicode_units("aİ😀") == [0x61, 0x130, 0xD83D, 0xDE00]


def test_keyboard_sink_write_does_not_use_keyboard_write(monkeypatch):
    import keyboard

    from kisayol import hook as hook_mod
    sent = []
    monkeypatch.setattr(hook_mod, "_send_unicode", lambda text, delay: sent.append((text, delay)))
    monkeypatch.setattr(keyboard, "write", lambda *a, **k: (_ for _ in ()).throw(AssertionError("keyboard.write")))
    hook_mod.KeyboardSink().write("Selamlar,", 3)
    assert sent == [("Selamlar,", 3)]


def test_keyboard_sink_tap_releases_modifier_on_error(monkeypatch):
    import keyboard

    from kisayol import hook as hook_mod
    events = []

    def press(k):
        events.append(("press", k))
        if k == "v":
            raise RuntimeError("boom")
    monkeypatch.setattr(keyboard, "press", press)
    monkeypatch.setattr(keyboard, "release", lambda k: events.append(("release", k)))
    monkeypatch.setattr(hook_mod.time, "sleep", lambda s: None)
    try:
        hook_mod.KeyboardSink().tap("ctrl+v")
    except RuntimeError:
        pass
    assert ("release", "ctrl") in events


def test_foreground_change_resyncs_stale_modifiers():
    hook, m, _, _ = make()
    hook._pressed = {"windows", "shift"}
    hook._key_is_down = lambda name: name == "shift"
    hook.on_foreground_change()
    assert hook._pressed == {"shift"}


def test_own_window_in_front_is_not_fed():
    hook, m, _, _ = make()
    hook.own_foreground = True
    hook.handle_key("a", "down", set())
    assert m.calls == []


def test_hotkey_problem_requires_real_modifier():
    from kisayol.hook import hotkey_problem
    assert hotkey_problem("a") == "err_hk_modifier"
    assert hotkey_problem("shift+a") == "err_hk_modifier"
    assert hotkey_problem("space") == "err_hk_modifier"
    assert hotkey_problem("f9") is None
    assert hotkey_problem("ctrl+alt+space") is None
    assert hotkey_problem("ctrl+@") == "err_hk_key"


def test_hotkey_problem_rejects_altgr_characters():
    from kisayol.hook import hotkey_problem
    assert hotkey_problem("ctrl+alt+q", altgr_char=lambda key: "@" if key == "q" else "") == "err_hk_altgr"
    assert hotkey_problem("ctrl+alt+p", altgr_char=lambda key: "") is None


def test_punctuation_keys_not_registered():
    from kisayol.hook import to_win_hotkey
    assert to_win_hotkey("ctrl+@") is None
