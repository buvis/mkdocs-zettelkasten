from __future__ import annotations

from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


class TestPreviewExporter:
    def setup_method(self) -> None:
        self.exporter = PreviewExporter()

    def test_export_returns_correct_structure(self) -> None:
        z1 = _make_zettel_mock(
            1, title="One", rel_path="notes/one.md",
            body="\n\nThis is the first paragraph for one.",
        )
        z2 = _make_zettel_mock(
            2, title="Two", rel_path="notes/two.md",
            body="\n\nThis is the first paragraph for two.",
        )
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

    def test_excerpt_truncated_at_200_chars(self) -> None:
        paragraph = (
            "alpha beta gamma delta epsilon zeta eta theta iota kappa lambda mu nu xi omicron "
            "pi rho sigma tau upsilon phi chi psi omega alpha beta gamma delta epsilon zeta eta "
            "theta iota kappa lambda mu nu xi omicron pi rho sigma tau upsilon phi chi psi omega"
        )
        store = ZettelStore(
            [_make_zettel_mock(3, title="Long", rel_path="long.md", body=f"\n\n{paragraph}")]
        )

        result = self.exporter.export(store)
        excerpt = result["3"]["excerpt"]

        assert excerpt.endswith("\u2026")
        assert len(excerpt) <= 201
        assert paragraph.startswith(excerpt[:-1])
        assert paragraph[len(excerpt[:-1])] == " "

    def test_headings_skipped(self) -> None:
        store = ZettelStore(
            [_make_zettel_mock(
                4, title="Heading", rel_path="heading.md",
                body="\n\n## Some Heading\n\nThis is the first paragraph.",
            )]
        )

        result = self.exporter.export(store)

        assert result["4"]["excerpt"] == "This is the first paragraph."

    def test_blank_lines_skipped(self) -> None:
        store = ZettelStore(
            [_make_zettel_mock(
                5, title="Blank", rel_path="blank.md",
                body="\n\n\n\n\nThis is the first paragraph after blank lines.",
            )]
        )

        result = self.exporter.export(store)

        assert result["5"]["excerpt"] == "This is the first paragraph after blank lines."

    def test_markdown_links_stripped(self) -> None:
        store = ZettelStore(
            [_make_zettel_mock(
                6, title="Links", rel_path="links.md",
                body="\n\nRead [the docs](https://example.com/docs) and [quickstart](quickstart.md).",
            )]
        )

        result = self.exporter.export(store)

        assert result["6"]["excerpt"] == "Read the docs and quickstart."

    def test_empty_body_returns_empty_excerpt(self) -> None:
        store = ZettelStore(
            [_make_zettel_mock(7, title="Empty", rel_path="empty.md", body="")]
        )

        result = self.exporter.export(store)

        assert result["7"]["excerpt"] == ""

    def test_multiple_zettels(self) -> None:
        store = ZettelStore(
            [
                _make_zettel_mock(8, title="A", rel_path="a.md", body="\n\nFirst paragraph A."),
                _make_zettel_mock(9, title="B", rel_path="b.md", body="\n\nFirst paragraph B."),
                _make_zettel_mock(10, title="C", rel_path="c.md", body="\n\nFirst paragraph C."),
            ]
        )

        result = self.exporter.export(store)

        assert set(result.keys()) == {"8", "9", "10"}

    def test_url_format(self) -> None:
        store = ZettelStore(
            [_make_zettel_mock(
                11, title="URL", rel_path="notes/nested/url.md",
                body="\n\nExcerpt text.",
            )]
        )

        result = self.exporter.export(store)

        assert result["11"]["url"] == "notes/nested/url/"
