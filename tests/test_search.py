from kisayol.search import filter_snippets
from kisayol.snippets import Snippet

ADR = Snippet(";adr", "Adres: Atatürk Cad.")
IMZA = Snippet(";imza", "Saygılarımla")
NOT = Snippet(";not", "imza gerekmez")


def test_turkish_case_insensitive_trigger():
    assert filter_snippets([ADR, IMZA], "İMZA") == [IMZA]


def test_text_match():
    assert filter_snippets([ADR, IMZA], "adres") == [ADR]
    assert filter_snippets([ADR, IMZA], "SAYGI") == [IMZA]


def test_empty_query_returns_all():
    assert filter_snippets([ADR, IMZA], "  ") == [ADR, IMZA]


def test_trigger_matches_first():
    assert filter_snippets([NOT, IMZA], "imza") == [IMZA, NOT]


def test_no_match():
    assert filter_snippets([ADR], "xyz") == []
