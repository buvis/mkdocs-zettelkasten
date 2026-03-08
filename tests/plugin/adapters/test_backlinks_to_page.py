from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.backlinks_to_page import (
    adapt_backlinks_to_page,
    add_backlink_to_target,
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
        zettel.link_snippets = {}
        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.rel_path = "target.md"
        zettel.rel_path = "source.md"

        zettel_by_id = MagicMock(return_value=target)

        add_backlink_to_target(42, page, zettel, zettel_by_id)
        assert len(target.backlinks) == 1
        assert target.backlinks[0]["url"] == "/page/"

    def test_skips_when_ids_differ(self) -> None:
        page = _make_page(zettel_id=1)
        zettel = MagicMock()
        zettel.id = 2

        zettel_by_id = MagicMock()
        add_backlink_to_target(42, page, zettel, zettel_by_id)
        zettel_by_id.assert_not_called()

    def test_skips_when_target_not_found(self) -> None:
        page = _make_page(zettel_id=1)
        zettel = MagicMock()
        zettel.id = 1

        zettel_by_id = MagicMock(return_value=None)

        add_backlink_to_target(42, page, zettel, zettel_by_id)
        zettel_by_id.assert_called_once_with(42)


class TestAdaptBacklinksToPage:
    def test_skips_non_zettel(self) -> None:
        page = _make_page(is_zettel=False)
        zettel_by_id = MagicMock()
        adapt_backlinks_to_page(page, {}, zettel_by_id)
        zettel_by_id.assert_not_called()

    def test_processes_backlinks(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.link_snippets = {}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.rel_path = "target.md"
        source_zettel.rel_path = "source.md"

        backlinks = {42: [source_zettel]}
        zettel_by_id = MagicMock(return_value=target)

        adapt_backlinks_to_page(page, backlinks, zettel_by_id)
        assert len(target.backlinks) == 1


class TestMocParents:
    def test_moc_source_populates_moc_parents(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = True
        source_zettel.rel_path = "moc.md"
        source_zettel.link_snippets = {}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert len(target.backlinks) == 1
        assert len(target.moc_parents) == 1
        assert target.moc_parents[0]["title"] == "Page Title"
        assert target.moc_parents[0]["url"] == "/page/"

    def test_non_moc_source_skips_moc_parents(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = False
        source_zettel.rel_path = "regular.md"
        source_zettel.link_snippets = {}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert len(target.backlinks) == 1
        assert len(target.moc_parents) == 0


class TestBacklinkSnippets:
    def test_snippet_found_by_target_id(self) -> None:
        """Wiki links store snippets keyed by target zettel ID."""
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = False
        source_zettel.rel_path = "source.md"
        source_zettel.link_snippets = {"42": "some context around the link"}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert target.backlinks[0]["snippet"] == "some context around the link"

    def test_snippet_found_by_rel_path(self) -> None:
        """MD links store snippets keyed by target rel_path."""
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = False
        source_zettel.rel_path = "source.md"
        source_zettel.link_snippets = {"target.md": "context via path"}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert target.backlinks[0]["snippet"] == "context via path"

    def test_snippet_found_by_rel_path_without_suffix(self) -> None:
        """Snippets keyed without suffix still resolve."""
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = False
        source_zettel.rel_path = "source.md"
        source_zettel.link_snippets = {"target": "context no suffix"}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert target.backlinks[0]["snippet"] == "context no suffix"

    def test_snippet_none_when_not_available(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = False
        source_zettel.rel_path = "source.md"
        source_zettel.link_snippets = {}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert target.backlinks[0]["snippet"] is None

    def test_moc_parent_also_gets_snippet(self) -> None:
        page = _make_page(zettel_id=1)
        source_zettel = MagicMock()
        source_zettel.id = 1
        source_zettel.is_moc = True
        source_zettel.rel_path = "moc.md"
        source_zettel.link_snippets = {"42": "MOC context snippet"}

        target = MagicMock()
        target.id = 42
        target.backlinks = []
        target.moc_parents = []
        target.rel_path = "target.md"

        zettel_by_id = MagicMock(return_value=target)
        add_backlink_to_target(42, page, source_zettel, zettel_by_id)

        assert target.moc_parents[0]["snippet"] == "MOC context snippet"
