from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(zettel_id: int, path: str, links: list[str]) -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = Path(path)
    z.links = links
    z.__hash__ = lambda self: hash(zettel_id)
    z.__eq__ = lambda self, other: getattr(other, "id", None) == zettel_id
    return z


class TestBacklinkProcessor:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = BacklinkProcessor.process(store)
        assert result == {}

    def test_creates_backlinks(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md", ["b.md"])
        z2 = _make_zettel(2, "/docs/b.md", [])

        store = ZettelStore([z1, z2])
        result = BacklinkProcessor.process(store)

        assert "b.md" in result
        assert z1 in result["b.md"]

    def test_normalizes_links_without_suffix(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md", ["b"])
        z2 = _make_zettel(2, "/docs/b.md", [])

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
        z1 = _make_zettel(1, "/docs/a.md", ["nonexistent"])
        store = ZettelStore([z1])
        result = BacklinkProcessor.process(store)
        assert result == {}
