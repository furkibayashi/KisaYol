from kisayol import themes


def test_all_themes_build_palette():
    for name in themes.THEMES:
        assert themes.palette(name)["accent"].startswith("#")
