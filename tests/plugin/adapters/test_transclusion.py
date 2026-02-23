from pathlib import Path

from mkdocs_zettelkasten.plugin.adapters.transclusion import _read_zettel_body


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
