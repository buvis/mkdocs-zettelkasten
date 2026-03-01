from mkdocs_zettelkasten.plugin.utils.snippet_utils import truncate_around


def test_short_text_returned_as_is() -> None:
    text = "short text"
    assert truncate_around(text, 0, 5) == text


def test_empty_string() -> None:
    assert truncate_around("", 0, 0) == ""


def test_position_at_start() -> None:
    text = "a " * 150  # 300 chars
    result = truncate_around(text, 0, 2)
    assert not result.startswith("...")
    assert result.endswith("...")


def test_position_at_end() -> None:
    text = "a " * 150
    result = truncate_around(text, 298, 2)
    assert result.startswith("...")
    assert not result.endswith("...")


def test_position_in_middle() -> None:
    text = "a " * 150
    result = truncate_around(text, 150, 2)
    assert result.startswith("...")
    assert result.endswith("...")


def test_marker_len_larger_than_text() -> None:
    text = "hello"
    assert truncate_around(text, 0, 999) == text


def test_exact_max_len() -> None:
    text = "x" * 200
    assert truncate_around(text, 0, 1) == text


def test_long_text_truncated_from_start() -> None:
    text = "x" * 400
    result = truncate_around(text, 300, 1)
    assert result.startswith("...")
    assert len(result) < len(text)


def test_word_boundary_expansion() -> None:
    words = "alpha bravo charlie delta echo foxtrot " * 8  # > 200 chars
    result = truncate_around(words, 100, 5)
    # Should not cut mid-word
    inner = result.lstrip(".").rstrip(".")
    assert not inner.startswith(" ")
