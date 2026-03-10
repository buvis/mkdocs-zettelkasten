from pathlib import Path

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


class TestBacklinkProcessor:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = BacklinkProcessor.process(store, {})
        assert result == {}

    def test_creates_backlinks(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        resolved = {1: {2}, 2: set()}
        result = BacklinkProcessor.process(store, resolved)

        assert 2 in result
        assert z1 in result[2]

    def test_no_backlinks_for_unresolved(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        store = ZettelStore([z1])

        result = BacklinkProcessor.process(store, {1: set()})
        assert result == {}

    def test_multiple_sources_to_same_target(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        z3 = _make_zettel_mock(3, path=Path("/docs/c.md"))
        store = ZettelStore([z1, z2, z3])

        resolved = {1: {3}, 2: {3}, 3: set()}
        result = BacklinkProcessor.process(store, resolved)

        assert len(result[3]) == 2
        assert z1 in result[3]
        assert z2 in result[3]

    def test_ignores_ids_not_in_store(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"))
        store = ZettelStore([z1])

        # resolved map references target 99 which isn't in store
        # BacklinkProcessor just builds the dict — it doesn't validate IDs
        result = BacklinkProcessor.process(store, {1: {99}})
        assert 99 in result
        assert z1 in result[99]
