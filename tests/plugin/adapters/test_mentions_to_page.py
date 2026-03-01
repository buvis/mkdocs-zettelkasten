from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.mentions_to_page import (
    adapt_mentions_to_page,
)


def _make_page(is_zettel: bool = True, zettel_id: int = 1) -> MagicMock:
    page = MagicMock()
    zettel = MagicMock()
    zettel.id = zettel_id
    page.meta = {"is_zettel": is_zettel, "zettel": zettel}
    page.url = "/source/"
    page.title = "Source Title"
    return page


class TestAdaptMentionsToPage:
    def test_skips_non_zettel(self) -> None:
        page = _make_page(is_zettel=False)
        mentions = {}
        adapt_mentions_to_page(page, mentions, lambda x: None)

    def test_adds_mention_to_target(self) -> None:
        page = _make_page(zettel_id=1)
        target = MagicMock()
        target.unlinked_mentions = []

        mentions = {99: [(1, "context <mark>snippet</mark>")]}
        zettel_lookup = MagicMock(return_value=target)

        adapt_mentions_to_page(page, mentions, zettel_lookup)

        assert len(target.unlinked_mentions) == 1
        assert target.unlinked_mentions[0]["url"] == "/source/"
        assert target.unlinked_mentions[0]["title"] == "Source Title"
        assert "<mark>" in target.unlinked_mentions[0]["snippet"]

    def test_skips_when_source_id_no_match(self) -> None:
        page = _make_page(zettel_id=1)
        target = MagicMock()
        target.unlinked_mentions = []

        mentions = {99: [(2, "snippet")]}
        zettel_lookup = MagicMock(return_value=target)

        adapt_mentions_to_page(page, mentions, zettel_lookup)
        assert len(target.unlinked_mentions) == 0

    def test_skips_when_target_not_found(self) -> None:
        page = _make_page(zettel_id=1)
        mentions = {99: [(1, "snippet")]}
        zettel_lookup = MagicMock(return_value=None)

        adapt_mentions_to_page(page, mentions, zettel_lookup)

    def test_skips_when_zettel_meta_missing(self) -> None:
        page = MagicMock()
        page.meta = {"is_zettel": True}
        adapt_mentions_to_page(page, {99: [(1, "snippet")]}, lambda x: None)

    def test_empty_mentions_dict(self) -> None:
        page = _make_page(zettel_id=1)
        target = MagicMock()
        target.unlinked_mentions = []
        adapt_mentions_to_page(page, {}, MagicMock(return_value=target))
        assert len(target.unlinked_mentions) == 0
