from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor
from mkdocs_zettelkasten.plugin.services.graph_exporter import GraphExporter
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(
    zettel_id: int, path: str, rel_path: str, title: str, links: list[str]
) -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = Path(path)
    z.rel_path = rel_path
    z.title = title
    z.links = links
    z.note_type = None
    z.maturity = None
    z.__hash__ = lambda self: hash(zettel_id)
    z.__eq__ = lambda self, other: getattr(other, "id", None) == zettel_id
    return z


def _build_backlinks(store: ZettelStore) -> dict:
    return BacklinkProcessor.process(store)


class TestGraphExporter:
    def setup_method(self) -> None:
        self.exporter = GraphExporter()

    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = self.exporter.export(store, [], {})
        assert result == {"nodes": [], "edges": []}

    def test_single_zettel_no_links(self) -> None:
        z = _make_zettel(
            20211122194827, "/docs/notes/install.md", "notes/install.md", "Install", []
        )
        store = ZettelStore([z])
        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 1
        assert result["nodes"][0] == {
            "id": "20211122194827",
            "title": "Install",
            "url": "notes/install/",
            "tags": [],
        }
        assert result["edges"] == []

    def test_two_zettels_with_link(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md", "a.md", "A", ["b.md"])
        z2 = _make_zettel(2, "/docs/b.md", "b.md", "B", [])
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1
        assert result["edges"][0] == {"source": "1", "target": "2"}

    def test_broken_link_skipped(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", ["nonexistent.md"])
        store = ZettelStore([z])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 1
        assert result["edges"] == []

    def test_duplicate_edges_deduplicated(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md", "a.md", "A", ["b.md", "b"])
        z2 = _make_zettel(2, "/docs/b.md", "b.md", "B", [])
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["edges"]) == 1

    def test_tags_from_metadata(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        store = ZettelStore([z])
        metadata = [{"src_path": "a.md", "tags": ["setup", "guide"]}]

        result = self.exporter.export(store, metadata, {})

        assert result["nodes"][0]["tags"] == ["setup", "guide"]

    def test_tags_missing_for_zettel(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["tags"] == []

    def test_url_computation(self) -> None:
        z = _make_zettel(1, "/docs/notes/foo.md", "notes/foo.md", "Foo", [])
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["url"] == "notes/foo/"

    def test_node_includes_type_when_present(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        z.note_type = "permanent"
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["type"] == "permanent"

    def test_node_includes_maturity_when_present(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        z.maturity = "evergreen"
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["maturity"] == "evergreen"

    def test_node_omits_type_when_none(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert "type" not in result["nodes"][0]

    def test_node_omits_maturity_when_none(self) -> None:
        z = _make_zettel(1, "/docs/a.md", "a.md", "A", [])
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert "maturity" not in result["nodes"][0]
