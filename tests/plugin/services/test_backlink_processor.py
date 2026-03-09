from pathlib import Path

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


class TestBacklinkProcessor:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = BacklinkProcessor.process(store)
        assert result == {}

    def test_creates_backlinks(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b.md"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))

        store = ZettelStore([z1, z2])
        result = BacklinkProcessor.process(store)

        assert 2 in result
        assert z1 in result[2]

    def test_normalizes_links_without_suffix(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))

        store = ZettelStore([z1, z2])
        result = BacklinkProcessor.process(store)

        assert 2 in result

    def test_normalize_links_appends_suffix(self) -> None:
        result = BacklinkProcessor.normalize_links(["a", "b.md"])
        assert result == {"a.md", "b.md"}

    def test_normalize_links_custom_suffix(self) -> None:
        result = BacklinkProcessor.normalize_links(["a", "b.txt"], file_suffix=".txt")
        assert result == {"a.txt", "b.txt"}

    def test_normalize_links_deduplicates(self) -> None:
        result = BacklinkProcessor.normalize_links(["a", "a.md"])
        assert result == {"a.md"}

    def test_ignores_unresolved_links(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["nonexistent"])
        store = ZettelStore([z1])
        result = BacklinkProcessor.process(store)
        assert result == {}


class TestBacklinkProcessorWithResolvedLinks:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = BacklinkProcessor.process(store, resolved_links={})
        assert result == {}

    def test_creates_backlinks_from_resolved_map(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        resolved = {1: {2}, 2: set()}
        result = BacklinkProcessor.process(store, resolved_links=resolved)

        assert 2 in result
        assert z1 in result[2]

    def test_no_store_lookup_when_resolved_provided(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b.md"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        # Pass empty resolved_links — should produce no backlinks
        # even though z1 links to b.md (proves store lookup is skipped)
        result = BacklinkProcessor.process(store, resolved_links={1: set(), 2: set()})
        assert result == {}

    def test_multiple_sources_to_same_target(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        z3 = _make_zettel_mock(3, path=Path("/docs/c.md"))
        store = ZettelStore([z1, z2, z3])

        resolved = {1: {3}, 2: {3}, 3: set()}
        result = BacklinkProcessor.process(store, resolved_links=resolved)

        assert len(result[3]) == 2
        assert z1 in result[3]
        assert z2 in result[3]
