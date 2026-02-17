from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.backlinks_to_page import (
    add_backlink_to_target,
    adapt_backlinks_to_page,
)


def _make_page(is_zettel: bool = True, zettel_id: int = 1) -> MagicMock:
    page = MagicMock()
    zettel = MagicMock()
    zettel.id = zettel_id
    page.meta = {"is_zettel": is_zettel, "zettel": zettel}
    page.url = "/page/"
    page.title = "Page Title"
    return page


class TestAddBacklinkToTarget:
    def test_adds_backlink_when_ids_match(self) -> None:
        page = _make_page(zettel_id=1)
        zettel = MagicMock()
        zettel.id = 1
        target = MagicMock()
        target.backlinks = []
        target.rel_path = "target.md"
        zettel.rel_path = "source.md"

        zettel_service = MagicMock()
        zettel_service.get_zettel_by_partial_path.return_value = target

        add_backlink_to_target("link", page, zettel, zettel_service)
        assert len(target.backlinks) == 1
        assert target.backlinks[0]["url"] == "/page/"

    def test_skips_when_ids_differ(self) -> None:
        page = _make_page(zettel_id=1)
        zettel = MagicMock()
        zettel.id = 2

        zettel_service = MagicMock()
        add_backlink_to_target("link", page, zettel, zettel_service)
        zettel_service.get_zettel_by_partial_path.assert_not_called()

    def test_skips_when_target_not_found(self) -> None:
        page = _make_page(zettel_id=1)
        zettel = MagicMock()
        zettel.id = 1

        zettel_service = MagicMock()
        zettel_service.get_zettel_by_partial_path.return_value = None

        add_backlink_to_target("link", page, zettel, zettel_service)


class TestAdaptBacklinksToPage:
    def test_skips_non_zettel(self) -> None:
        page = _make_page(is_zettel=False)
        zettel_service = MagicMock()
        adapt_backlinks_to_page(page, zettel_service)
        # Should not iterate backlinks

    def test_processes_backlinks(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1

        target = MagicMock()
        target.backlinks = []
        target.rel_path = "target.md"
        source_zettel.rel_path = "source.md"

        zettel_service = MagicMock()
        zettel_service.backlinks = {"link1": [source_zettel]}
        zettel_service.get_zettel_by_partial_path.return_value = target

        adapt_backlinks_to_page(page, zettel_service)
        assert len(target.backlinks) == 1
