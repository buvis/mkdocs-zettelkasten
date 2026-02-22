from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.page_links_to_zettels import (
    adapt_page_links_to_zettels,
)


def _make_file(src_path: str, url: str) -> MagicMock:
    f = MagicMock()
    f.src_path = src_path
    f.url = url
    f.page = MagicMock()
    return f


def _make_context(site_url: str = "https://example.com/"):
    page = MagicMock()
    page.file.src_path = "current.md"

    config = MagicMock()
    config.__getitem__ = lambda self, key: {"site_url": site_url}[key]

    return page, config


class TestAdaptPageLinksToZettels:
    def test_rewrites_wiki_link_with_alias(self) -> None:
        page, config = _make_context()
        f = _make_file("target.md", "target/")
        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        zettel_lookup = MagicMock()

        result = adapt_page_links_to_zettels(
            "see [[target|my alias]]", page, config, files, zettel_lookup
        )
        assert "[my alias](https://example.com/target/)" in result

    def test_rewrites_md_link(self) -> None:
        page, config = _make_context()
        f = _make_file("note.md", "note/")
        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        zettel_lookup = MagicMock(return_value=None)

        result = adapt_page_links_to_zettels(
            "[my text](note.md)", page, config, files, zettel_lookup
        )
        assert "[my text](https://example.com/note/)" in result

    def test_skips_links_in_code_fences(self) -> None:
        page, config = _make_context()
        files = MagicMock()
        files.__iter__ = lambda self: iter([])

        zettel_lookup = MagicMock()

        md = "text\n```\n[[should_not_change]]\n```\nafter"
        result = adapt_page_links_to_zettels(md, page, config, files, zettel_lookup)
        assert "[[should_not_change]]" in result

    def test_unresolved_md_link_keeps_text(self) -> None:
        page, config = _make_context()
        files = MagicMock()
        files.__iter__ = lambda self: iter([])

        zettel_lookup = MagicMock()

        result = adapt_page_links_to_zettels(
            "[my text](nonexistent)", page, config, files, zettel_lookup
        )
        assert "[my text](nonexistent)" in result

    def test_md_link_substitutes_zettel_title(self) -> None:
        page, config = _make_context()
        f = _make_file("note.md", "note/")
        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        target = MagicMock()
        target.title = "Zettel Title"
        zettel_lookup = MagicMock(return_value=target)

        result = adapt_page_links_to_zettels(
            "[note.md](note.md)", page, config, files, zettel_lookup
        )
        assert "[Zettel Title](https://example.com/note/)" in result
