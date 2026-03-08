from pathlib import Path

from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor
from mkdocs_zettelkasten.plugin.services.graph_exporter import GraphExporter
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


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
        z = _make_zettel_mock(
            20211122194827,
            title="Install",
            rel_path="notes/install.md",
            path=Path("/docs/notes/install.md"),
        )
        store = ZettelStore([z])
        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 1
        assert result["nodes"][0] == {
            "id": "20211122194827",
            "title": "Install",
            "url": "notes/install/",
            "tags": [],
            "degree": 0,
        }
        assert result["edges"] == []

    def test_two_zettels_with_link(self) -> None:
        z1 = _make_zettel_mock(
            1, title="A", rel_path="a.md", path=Path("/docs/a.md"), links=["b.md"]
        )
        z2 = _make_zettel_mock(2, title="B", rel_path="b.md", path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 2
        assert len(result["edges"]) == 1
        assert result["edges"][0] == {"source": "1", "target": "2"}

    def test_broken_link_skipped(self) -> None:
        z = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            path=Path("/docs/a.md"),
            links=["nonexistent.md"],
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["nodes"]) == 1
        assert result["edges"] == []

    def test_duplicate_edges_deduplicated(self) -> None:
        z1 = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            path=Path("/docs/a.md"),
            links=["b.md", "b"],
        )
        z2 = _make_zettel_mock(2, title="B", rel_path="b.md", path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        assert len(result["edges"]) == 1

    def test_tags_from_metadata(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])
        metadata = [{"src_path": "a.md", "tags": ["setup", "guide"]}]

        result = self.exporter.export(store, metadata, {})

        assert result["nodes"][0]["tags"] == ["setup", "guide"]

    def test_tags_missing_for_zettel(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["tags"] == []

    def test_url_computation(self) -> None:
        z = _make_zettel_mock(
            1,
            title="Foo",
            rel_path="notes/foo.md",
            path=Path("/docs/notes/foo.md"),
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["url"] == "notes/foo/"

    def test_node_includes_type_when_present(self) -> None:
        z = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            path=Path("/docs/a.md"),
            note_type="permanent",
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["type"] == "permanent"

    def test_node_includes_maturity_when_present(self) -> None:
        z = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            path=Path("/docs/a.md"),
            maturity="evergreen",
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["maturity"] == "evergreen"

    def test_node_omits_type_when_none(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert "type" not in result["nodes"][0]

    def test_node_omits_maturity_when_none(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert "maturity" not in result["nodes"][0]

    def test_node_includes_role_when_present(self) -> None:
        z = _make_zettel_mock(
            1, title="A", rel_path="a.md", path=Path("/docs/a.md"), role="moc"
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["role"] == "moc"

    def test_node_omits_role_when_none(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert "role" not in result["nodes"][0]

    def test_sequence_edges_exported(self) -> None:
        z1 = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(
            2,
            title="B",
            rel_path="b.md",
            path=Path("/docs/b.md"),
            sequence_parent_id=1,
        )
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        seq_edges = [e for e in result["edges"] if e.get("type") == "sequence"]
        assert len(seq_edges) == 1
        assert seq_edges[0]["source"] == "2"
        assert seq_edges[0]["target"] == "1"

    def test_sequence_edge_skipped_when_parent_missing(self) -> None:
        z = _make_zettel_mock(
            1,
            title="A",
            rel_path="a.md",
            path=Path("/docs/a.md"),
            sequence_parent_id=999,
        )
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        seq_edges = [e for e in result["edges"] if e.get("type") == "sequence"]
        assert seq_edges == []

    def test_node_degree_with_links(self) -> None:
        z1 = _make_zettel_mock(
            1, title="A", rel_path="a.md", path=Path("/docs/a.md"), links=["b.md"]
        )
        z2 = _make_zettel_mock(
            2, title="B", rel_path="b.md", path=Path("/docs/b.md"), links=["a.md"]
        )
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        degrees = {n["id"]: n["degree"] for n in result["nodes"]}
        assert degrees["1"] == 2
        assert degrees["2"] == 2

    def test_node_degree_no_links(self) -> None:
        z = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        store = ZettelStore([z])

        result = self.exporter.export(store, [], {})

        assert result["nodes"][0]["degree"] == 0

    def test_node_degree_counts_sequence_edges(self) -> None:
        z1 = _make_zettel_mock(1, title="A", rel_path="a.md", path=Path("/docs/a.md"))
        z2 = _make_zettel_mock(
            2,
            title="B",
            rel_path="b.md",
            path=Path("/docs/b.md"),
            sequence_parent_id=1,
        )
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        degrees = {n["id"]: n["degree"] for n in result["nodes"]}
        assert degrees["1"] == 1
        assert degrees["2"] == 1

    def test_overlapping_backlink_and_sequence_both_preserved(self) -> None:
        z1 = _make_zettel_mock(
            1, title="Parent", rel_path="a.md", path=Path("/docs/a.md")
        )
        z2 = _make_zettel_mock(
            2,
            title="Child",
            rel_path="b.md",
            path=Path("/docs/b.md"),
            links=["a.md"],
            sequence_parent_id=1,
        )
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        backlink_edges = [e for e in result["edges"] if "type" not in e]
        seq_edges = [e for e in result["edges"] if e.get("type") == "sequence"]
        assert len(backlink_edges) == 1
        assert len(seq_edges) == 1
        assert backlink_edges[0] == {"source": "2", "target": "1"}
        assert seq_edges[0] == {"source": "2", "target": "1", "type": "sequence"}

    def test_link_edges_have_no_type(self) -> None:
        z1 = _make_zettel_mock(
            1, title="A", rel_path="a.md", path=Path("/docs/a.md"), links=["b.md"]
        )
        z2 = _make_zettel_mock(2, title="B", rel_path="b.md", path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = self.exporter.export(store, [], _build_backlinks(store))

        link_edges = [e for e in result["edges"] if "type" not in e]
        assert len(link_edges) == 1
