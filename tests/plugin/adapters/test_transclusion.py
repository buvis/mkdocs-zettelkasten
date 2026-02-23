from pathlib import Path

from mkdocs_zettelkasten.plugin.adapters.transclusion import (
    _extract_section,
    _read_zettel_body,
)


class TestReadZettelBody:
    def test_strips_yaml_frontmatter(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\ntitle: Test\n---\n\n# Title\n\nBody text.\n")
        assert _read_zettel_body(f) == "\n# Title\n\nBody text.\n"

    def test_strips_reference_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\n---\n\nBody.\n---\nref: foo\n---\n")
        assert _read_zettel_body(f) == "\nBody.\n"

    def test_returns_empty_for_header_only(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\n---\n")
        assert _read_zettel_body(f) == ""


class TestExtractSection:
    def test_extracts_h2_section(self) -> None:
        body = "## Intro\n\nFirst.\n\n## Details\n\nSecond.\n"
        assert _extract_section(body, "Intro") == "## Intro\n\nFirst.\n\n"

    def test_extracts_last_section(self) -> None:
        body = "## Intro\n\nFirst.\n\n## Details\n\nSecond.\n"
        assert _extract_section(body, "Details") == "## Details\n\nSecond.\n"

    def test_case_insensitive_match(self) -> None:
        body = "## My Section\n\nContent.\n"
        assert _extract_section(body, "my section") == "## My Section\n\nContent.\n"

    def test_stops_at_same_level_heading(self) -> None:
        body = "## A\n\nText.\n\n### Sub\n\nDeep.\n\n## B\n\nOther.\n"
        result = _extract_section(body, "A")
        assert "### Sub" in result
        assert "## B" not in result

    def test_returns_none_when_not_found(self) -> None:
        body = "## Intro\n\nText.\n"
        assert _extract_section(body, "Nonexistent") is None
