from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock

if TYPE_CHECKING:
    from pathlib import Path

from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(zettel_id: int, path: Path, rel_path: str, title: str) -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = path
    z.rel_path = rel_path
    z.title = title
    return z


def _write_zettel(tmp_path: Path, name: str, zettel_id: int, title: str, body: str) -> Path:
    path = tmp_path / name
    path.write_text(
        f"---\nid: {zettel_id}\ntitle: {title}\n---\n\n{body}",
        encoding="utf-8",
    )
    return path


class TestPreviewExporter:
    def setup_method(self) -> None:
        self.exporter = PreviewExporter()

    def test_export_returns_correct_structure(self, tmp_path: Path) -> None:
        z1_path = _write_zettel(
            tmp_path,
            "one.md",
            1,
            "One",
            "This is the first paragraph for one.",
        )
        z2_path = _write_zettel(
            tmp_path,
            "two.md",
            2,
            "Two",
            "This is the first paragraph for two.",
        )
        z1 = _make_zettel(1, z1_path, "notes/one.md", "One")
        z2 = _make_zettel(2, z2_path, "notes/two.md", "Two")
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store)

        assert result == {
            "1": {
                "title": "One",
                "excerpt": "This is the first paragraph for one.",
                "url": "notes/one/",
            },
            "2": {
                "title": "Two",
                "excerpt": "This is the first paragraph for two.",
                "url": "notes/two/",
            },
        }

    def test_excerpt_truncated_at_200_chars(self, tmp_path: Path) -> None:
        paragraph = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron "
            "pi rho sigma tau upsilon phi chi psi omega alpha beta gamma delta epsilon zeta eta "
            "theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega"
        )
        z_path = _write_zettel(tmp_path, "long.md", 3, "Long", paragraph)
        store = ZettelStore([_make_zettel(3, z_path, "long.md", "Long")])

        result = self.exporter.export(store)
        excerpt = result["3"]["excerpt"]

        assert excerpt.endswith("…")
        assert len(excerpt) <= 201
        assert paragraph.startswith(excerpt[:-1])
        assert paragraph[len(excerpt[:-1])] == " "

    def test_headings_skipped(self, tmp_path: Path) -> None:
        z_path = _write_zettel(
            tmp_path,
            "heading.md",
            4,
            "Heading",
            "## Some Heading\n\nThis is the first paragraph.",
        )
        store = ZettelStore([_make_zettel(4, z_path, "heading.md", "Heading")])

        result = self.exporter.export(store)

        assert result["4"]["excerpt"] == "This is the first paragraph."

    def test_blank_lines_skipped(self, tmp_path: Path) -> None:
        z_path = _write_zettel(
            tmp_path,
            "blank.md",
            5,
            "Blank",
            "\n\n\nThis is the first paragraph after blank lines.",
        )
        store = ZettelStore([_make_zettel(5, z_path, "blank.md", "Blank")])

        result = self.exporter.export(store)

        assert result["5"]["excerpt"] == "This is the first paragraph after blank lines."

    def test_markdown_links_stripped(self, tmp_path: Path) -> None:
        z_path = _write_zettel(
            tmp_path,
            "links.md",
            6,
            "Links",
            "Read [the docs](https://example.com/docs) and [quickstart](quickstart.md).",
        )
        store = ZettelStore([_make_zettel(6, z_path, "links.md", "Links")])

        result = self.exporter.export(store)

        assert result["6"]["excerpt"] == "Read the docs and quickstart."

    def test_empty_body_returns_empty_excerpt(self, tmp_path: Path) -> None:
        z_path = _write_zettel(tmp_path, "empty.md", 7, "Empty", "")
        store = ZettelStore([_make_zettel(7, z_path, "empty.md", "Empty")])

        result = self.exporter.export(store)

        assert result["7"]["excerpt"] == ""

    def test_multiple_zettels(self, tmp_path: Path) -> None:
        z1_path = _write_zettel(tmp_path, "a.md", 8, "A", "First paragraph A.")
        z2_path = _write_zettel(tmp_path, "b.md", 9, "B", "First paragraph B.")
        z3_path = _write_zettel(tmp_path, "c.md", 10, "C", "First paragraph C.")
        store = ZettelStore(
            [
                _make_zettel(8, z1_path, "a.md", "A"),
                _make_zettel(9, z2_path, "b.md", "B"),
                _make_zettel(10, z3_path, "c.md", "C"),
            ]
        )

        result = self.exporter.export(store)

        assert set(result.keys()) == {"8", "9", "10"}

    def test_url_format(self, tmp_path: Path) -> None:
        z_path = _write_zettel(tmp_path, "url.md", 11, "URL", "Excerpt text.")
        store = ZettelStore([_make_zettel(11, z_path, "notes/nested/url.md", "URL")])

        result = self.exporter.export(store)

        assert result["11"]["url"] == "notes/nested/url/"
