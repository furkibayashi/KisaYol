from kisayol.matcher import BUFFER_MAX, Match, Matcher
from kisayol.snippets import Snippet


def make(*triggers, disabled=()):
    m = Matcher()
    snips = [Snippet(t, t.upper()) for t in triggers]
    snips += [Snippet(t, t.upper(), enabled=False) for t in disabled]
    m.set_snippets(snips)
    return m


def type_all(m, text):
    result = None
    for ch in text:
        result = m.feed(ch)
    return result


def test_symbol_fires_immediately():
    m = make(";adr")
    assert m.feed(";") is None
    assert m.feed("a") is None
    assert m.feed("d") is None
    hit = m.feed("r")
    assert isinstance(hit, Match)
    assert (hit.snippet.trigger, hit.delete_count, hit.suffix) == (";adr", 4, "")


def test_buffer_resets_after_match():
    m = make(";adr")
    type_all(m, ";adr")
    assert m.buffer == ""


def test_longest_symbol_wins():
    m = make("!dr", ";!dr")
    hit = type_all(m, ";!dr")
    assert (hit.snippet.trigger, hit.delete_count) == (";!dr", 4)


def test_bare_needs_terminator_and_keeps_it():
    m = make("slm")
    assert type_all(m, "slm") is None
    hit = m.feed(",")
    assert (hit.snippet.trigger, hit.delete_count, hit.suffix) == ("slm", 4, ",")


def test_bare_not_inside_word():
    m = make("slm")
    assert type_all(m, "Paslm ") is None


def test_bare_after_reset_is_word_start():
    m = make("slm")
    type_all(m, "Pa")
    m.reset()
    assert type_all(m, "slm ") is not None


def test_bare_after_punctuation():
    m = make("slm")
    hit = type_all(m, "x;slm ")
    assert hit is not None and hit.suffix == " "


def test_bare_after_space_mid_sentence():
    m = make("slm")
    hit = type_all(m, "naber slm.")
    assert (hit.delete_count, hit.suffix) == (4, ".")


def test_backspace_edits_buffer():
    m = make(";adr")
    type_all(m, ";adx")
    m.backspace()
    assert m.feed("r") is not None


def test_backspace_on_empty_buffer_is_safe():
    m = make(";adr")
    m.backspace()
    assert m.buffer == ""


def test_turkish_letters():
    m = make("şğü", ";ığ")
    assert type_all(m, "şğü ") is not None
    assert type_all(m, ";ığ") is not None


def test_case_sensitive():
    m = make("slm")
    assert type_all(m, "SLM ") is None


def test_buffer_capped():
    m = make(";zz")
    type_all(m, "a" * 200)
    assert len(m.buffer) == BUFFER_MAX


def test_truncated_word_not_word_start():
    m = make("slm")
    # 70 harflik tek kelime: tampon baştan kırpılsa da "slm" kelime başı sayılmamalı
    assert type_all(m, "a" * 67 + "slm ") is None


def test_disabled_snippets_ignored():
    m = make(disabled=(";adr", "slm"))
    assert type_all(m, ";adr") is None
    assert type_all(m, " slm ") is None


def test_enter_like_terminator_not_in_set():
    m = make("slm")
    assert type_all(m, "slm\n") is None
