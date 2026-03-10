import logging
from pathlib import Path

from mkdocs_zettelkasten.plugin.utils.metadata_utils import extract_file_metadata


def test_extracts_valid_yaml(tmp_path: Path) -> None:
    md = tmp_path / "note.md"
    md.write_text("---\nid: 123\ntitle: Test\n---\nBody text\n")

    meta = extract_file_metadata("note.md", str(tmp_path))
    assert meta["id"] == 123
    assert meta["title"] == "Test"


def test_returns_empty_for_missing_file(tmp_path: Path) -> None:
    meta = extract_file_metadata("nonexistent.md", str(tmp_path))
    assert meta == {}


def test_returns_empty_for_no_frontmatter(tmp_path: Path) -> None:
    md = tmp_path / "plain.md"
    md.write_text("Just plain text, no frontmatter\n")

    meta = extract_file_metadata("plain.md", str(tmp_path))
    assert meta == {}


def test_returns_empty_for_invalid_yaml(tmp_path: Path) -> None:
    md = tmp_path / "bad.md"
    md.write_text("---\n: invalid: yaml: here\n---\nBody\n")

    meta = extract_file_metadata("bad.md", str(tmp_path))
    assert meta == {}


def test_no_frontmatter_logs_debug(tmp_path: Path, caplog: object) -> None:
    md = tmp_path / "plain.md"
    md.write_text("Just plain text\n")
    with caplog.at_level(logging.DEBUG):  # type: ignore[union-attr]
        extract_file_metadata("plain.md", str(tmp_path))
    assert any(r.levelno == logging.DEBUG and "No YAML frontmatter" in r.message for r in caplog.records)  # type: ignore[union-attr]
    assert not any(r.levelno >= logging.WARNING and "frontmatter" in r.message.lower() for r in caplog.records)  # type: ignore[union-attr]


def test_unclosed_frontmatter_logs_warning(tmp_path: Path, caplog: object) -> None:
    md = tmp_path / "broken.md"
    md.write_text("---\nid: 1\n")
    with caplog.at_level(logging.DEBUG):  # type: ignore[union-attr]
        extract_file_metadata("broken.md", str(tmp_path))
    assert any(r.levelno == logging.WARNING and "Unclosed" in r.message for r in caplog.records)  # type: ignore[union-attr]


def test_handles_tags_list(tmp_path: Path) -> None:
    md = tmp_path / "tagged.md"
    md.write_text("---\nid: 1\ntags:\n  - foo\n  - bar\n---\nBody\n")

    meta = extract_file_metadata("tagged.md", str(tmp_path))
    assert meta["tags"] == ["foo", "bar"]
