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

        assert "b.md" in result
        assert z1 in result["b.md"]

    def test_normalizes_links_without_suffix(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))

        store = ZettelStore([z1, z2])
        result = BacklinkProcessor.process(store)

        assert "b.md" in result

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
