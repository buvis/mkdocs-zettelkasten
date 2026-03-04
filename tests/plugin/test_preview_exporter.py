from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import patch

if TYPE_CHECKING:
    from pathlib import Path

from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


def _write_zettel(
    tmp_path: Path, name: str, zettel_id: int, title: str, body: str
) -> Path:
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
            tmp_path, "one.md", 1, "One", "This is the first paragraph for one."
        )
        z2_path = _write_zettel(
            tmp_path, "two.md", 2, "Two", "This is the first paragraph for two."
        )
        z1 = _make_zettel_mock(1, title="One", path=z1_path, rel_path="notes/one.md")
        z2 = _make_zettel_mock(2, title="Two", path=z2_path, rel_path="notes/two.md")
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
        store = ZettelStore(
            [_make_zettel_mock(3, title="Long", path=z_path, rel_path="long.md")]
        )

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
        store = ZettelStore(
            [_make_zettel_mock(4, title="Heading", path=z_path, rel_path="heading.md")]
        )

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
        store = ZettelStore(
            [_make_zettel_mock(5, title="Blank", path=z_path, rel_path="blank.md")]
        )

        result = self.exporter.export(store)

        assert (
            result["5"]["excerpt"] == "This is the first paragraph after blank lines."
        )

    def test_markdown_links_stripped(self, tmp_path: Path) -> None:
        z_path = _write_zettel(
            tmp_path,
            "links.md",
            6,
            "Links",
            "Read [the docs](https://example.com/docs) and [quickstart](quickstart.md).",
        )
        store = ZettelStore(
            [_make_zettel_mock(6, title="Links", path=z_path, rel_path="links.md")]
        )

        result = self.exporter.export(store)

        assert result["6"]["excerpt"] == "Read the docs and quickstart."

    def test_empty_body_returns_empty_excerpt(self, tmp_path: Path) -> None:
        z_path = _write_zettel(tmp_path, "empty.md", 7, "Empty", "")
        store = ZettelStore(
            [_make_zettel_mock(7, title="Empty", path=z_path, rel_path="empty.md")]
        )

        result = self.exporter.export(store)

        assert result["7"]["excerpt"] == ""

    def test_multiple_zettels(self, tmp_path: Path) -> None:
        z1_path = _write_zettel(tmp_path, "a.md", 8, "A", "First paragraph A.")
        z2_path = _write_zettel(tmp_path, "b.md", 9, "B", "First paragraph B.")
        z3_path = _write_zettel(tmp_path, "c.md", 10, "C", "First paragraph C.")
        store = ZettelStore(
            [
                _make_zettel_mock(8, title="A", path=z1_path, rel_path="a.md"),
                _make_zettel_mock(9, title="B", path=z2_path, rel_path="b.md"),
                _make_zettel_mock(10, title="C", path=z3_path, rel_path="c.md"),
            ]
        )

        result = self.exporter.export(store)

        assert set(result.keys()) == {"8", "9", "10"}

    def test_url_format(self, tmp_path: Path) -> None:
        z_path = _write_zettel(tmp_path, "url.md", 11, "URL", "Excerpt text.")
        store = ZettelStore(
            [
                _make_zettel_mock(
                    11, title="URL", path=z_path, rel_path="notes/nested/url.md"
                )
            ]
        )

        result = self.exporter.export(store)

        assert result["11"]["url"] == "notes/nested/url/"

    def test_oserror_logs_warning(self, tmp_path: Path) -> None:
        z = _make_zettel_mock(
            12, title="Missing", path=tmp_path / "missing.md", rel_path="missing.md"
        )
        store = ZettelStore([z])

        with patch(
            "mkdocs_zettelkasten.plugin.services.preview_exporter.logger"
        ) as mock_logger:
            result = self.exporter.export(store)

        assert result["12"]["excerpt"] == ""
        mock_logger.warning.assert_called_once()
        assert "Cannot read" in mock_logger.warning.call_args[0][0]
