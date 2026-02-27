from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.suggestions_to_page import (
    adapt_suggestions_to_page,
)


def _make_page(zettel_id):
    page = MagicMock()
    zettel = MagicMock()
    zettel.id = zettel_id
    zettel.suggested_links = []
    page.meta = {"is_zettel": True, "zettel": zettel}
    return page, zettel


def _make_zettel_lookup(zettels):
    mapping = {z.id: z for z in zettels}
    return mapping.get


def _make_target(zettel_id, title, rel_path):
    z = MagicMock()
    z.id = zettel_id
    z.title = title
    z.rel_path = rel_path
    return z


class TestSuggestionsToPage:
    def test_attaches_suggestions_to_zettel(self):
        page, zettel = _make_page(1)
        target = _make_target(2, "Target Note", "target.md")
        suggestions = {
            1: [{"target_id": 2, "reason": "2 shared links", "confidence": 0.75}],
        }
        adapt_suggestions_to_page(page, suggestions, _make_zettel_lookup([target]))
        assert len(zettel.suggested_links) == 1
        assert zettel.suggested_links[0]["title"] == "Target Note"
        assert zettel.suggested_links[0]["reason"] == "2 shared links"
        assert zettel.suggested_links[0]["confidence"] == "75%"

    def test_url_computed_from_rel_path(self):
        page, zettel = _make_page(1)
        target = _make_target(2, "T", "notes/target.md")
        suggestions = {
            1: [{"target_id": 2, "reason": "1 shared tag", "confidence": 0.5}],
        }
        adapt_suggestions_to_page(page, suggestions, _make_zettel_lookup([target]))
        assert zettel.suggested_links[0]["url"] == "notes/target/"

    def test_skips_non_zettel_pages(self):
        page = MagicMock()
        page.meta = {"is_zettel": False}
        adapt_suggestions_to_page(page, {}, lambda x: None)
        # Should not raise

    def test_skips_missing_target(self):
        page, zettel = _make_page(1)
        suggestions = {
            1: [{"target_id": 999, "reason": "test", "confidence": 0.5}],
        }
        adapt_suggestions_to_page(page, suggestions, lambda x: None)
        assert len(zettel.suggested_links) == 0

    def test_no_suggestions_for_zettel(self):
        page, zettel = _make_page(1)
        adapt_suggestions_to_page(page, {}, lambda x: None)
        assert len(zettel.suggested_links) == 0
