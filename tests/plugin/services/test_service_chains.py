"""Integration tests for service chains.

These tests wire real services together with real Zettel objects
(created from actual markdown files on disk) to verify end-to-end
data flow across service boundaries.
"""

from __future__ import annotations

from typing import TYPE_CHECKING
from unittest.mock import MagicMock, patch

import pytest

from mkdocs_zettelkasten.plugin.services.graph_exporter import GraphExporter
from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter
from mkdocs_zettelkasten.plugin.services.suggestion_service import SuggestionService
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

if TYPE_CHECKING:
    from pathlib import Path

PERMISSIVE_CONFIG = {"id_format": r"^\d+$"}

# -- Zettel markdown fixtures ------------------------------------------------

ZETTEL_A = """\
---
id: 1
date: 2024-01-01
type: permanent
maturity: evergreen
---
# Alpha Note

This note links to [[2]] and mentions Gamma Note in passing.
"""

ZETTEL_B = """\
---
id: 2
date: 2024-01-02
type: literature
source: https://example.com
---
# Beta Note

A standalone note that links to [[1]].
"""

ZETTEL_C = """\
---
id: 3
date: 2024-01-03
type: fleeting
---
# Gamma Note

This note has no outgoing links but mentions Alpha Note.
"""

ZETTEL_SEQ_ROOT = """\
---
id: 10
date: 2024-02-01
---
# Sequence Root

Root of a Folgezettel sequence.
"""

ZETTEL_SEQ_CHILD = """\
---
id: 11
date: 2024-02-02
sequence: 10
---
# Sequence Child

Child note linking back to root via sequence.
"""

ZETTEL_SEQ_GRANDCHILD = """\
---
id: 12
date: 2024-02-03
sequence: 11
---
# Sequence Grandchild

Second level in the sequence hierarchy.
"""


# -- Helpers ------------------------------------------------------------------


def _write_zettel(docs_dir: Path, name: str, content: str) -> None:
    fp = docs_dir / name
    fp.write_text(content)


def _make_files(docs_dir: Path, file_map: dict[str, str]):
    """Create MagicMock Files from a {filename: content} mapping."""
    for name, content in file_map.items():
        _write_zettel(docs_dir, name, content)

    mock_files = []
    for name in file_map:
        f = MagicMock()
        f.src_path = name
        f.abs_src_path = str(docs_dir / name)
        f.is_documentation_page.return_value = True
        f.url = name.removesuffix(".md") + "/"
        f.page = None  # adapters check f.page for title resolution
        mock_files.append(f)

    files = MagicMock()
    files.__iter__ = lambda self: iter(mock_files)
    files.__len__ = lambda self: len(mock_files)
    return files, mock_files


def _make_config(docs_dir: Path):
    config = MagicMock()
    config.__getitem__ = lambda self, key: {"docs_dir": str(docs_dir)}[key]
    return config


def _make_full_config(docs_dir: Path):
    """Config dict supporting all keys the adapters access."""
    data = {
        "docs_dir": str(docs_dir),
        "site_url": "http://localhost/",
        "markdown_extensions": [],
        "mdx_configs": {},
    }
    config = MagicMock()
    config.__getitem__ = lambda self, key: data[key]
    config.get = lambda key, default=None: data.get(key, default)
    return config


def _build_service(docs_dir: Path, file_map: dict[str, str]):
    """Build a fully-processed ZettelService from markdown files."""
    files, _ = _make_files(docs_dir, file_map)
    config = _make_config(docs_dir)

    svc = ZettelService()
    svc.configure(PERMISSIVE_CONFIG)
    with patch(
        "mkdocs_zettelkasten.plugin.entities.zettel.GitUtil.is_tracked",
        return_value=False,
    ):
        svc.process_files(files, config)
    return svc


# -- Tests: ZettelService pipeline -------------------------------------------


class TestZettelServicePipeline:
    """process_files → store + backlinks + unlinked mentions + sequences."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        self.svc = _build_service(
            tmp_path,
            {"1.md": ZETTEL_A, "2.md": ZETTEL_B, "3.md": ZETTEL_C},
        )

    def test_store_populated(self) -> None:
        assert len(self.svc.get_zettels()) == 3

    def test_backlinks_computed(self) -> None:
        # A links to B, B links to A → both should have backlink entries
        assert len(self.svc.backlinks) > 0

    def test_backlink_targets_resolve(self) -> None:
        for link_path, sources in self.svc.backlinks.items():
            target = self.svc.store.get_by_partial_path(link_path)
            assert target is not None, f"backlink target {link_path} not in store"
            for src in sources:
                assert src in self.svc.store.zettels

    def test_unlinked_mentions_detected(self) -> None:
        # A mentions "Gamma Note" without linking → should detect mention on zettel 3
        assert len(self.svc.unlinked_mentions) > 0

    def test_unlinked_mentions_have_snippets(self) -> None:
        for mentions in self.svc.unlinked_mentions.values():
            for source_id, snippet in mentions:
                assert isinstance(source_id, int)
                assert len(snippet) > 0


class TestSequenceChain:
    """process_files → sequence tree for Folgezettel hierarchy."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path: Path) -> None:
        self.svc = _build_service(
            tmp_path,
            {
                "10.md": ZETTEL_SEQ_ROOT,
                "11.md": ZETTEL_SEQ_CHILD,
                "12.md": ZETTEL_SEQ_GRANDCHILD,
            },
        )

    def test_sequence_children_built(self) -> None:
        assert 10 in self.svc.sequence_children
        assert 11 in self.svc.sequence_children[10]

    def test_sequence_grandchild(self) -> None:
        assert 11 in self.svc.sequence_children
        assert 12 in self.svc.sequence_children[11]

    def test_root_has_no_parent(self) -> None:
        root = self.svc.get_zettel_by_id(10)
        assert root is not None
        assert root.sequence_parent_id is None


# -- Tests: Export chains -----------------------------------------------------


class TestGraphExportChain:
    """ZettelService → GraphExporter produces valid graph data."""

    def test_graph_nodes_and_edges(self, tmp_path: Path) -> None:
        svc = _build_service(tmp_path, {"1.md": ZETTEL_A, "2.md": ZETTEL_B})
        exporter = GraphExporter()
        tags_metadata = [
            {"src_path": "1.md", "tags": ["test"]},
            {"src_path": "2.md", "tags": ["test", "lit"]},
        ]

        graph = exporter.export(svc.store, tags_metadata, svc.backlinks)

        assert len(graph["nodes"]) == 2
        node_ids = {n["id"] for n in graph["nodes"]}
        assert node_ids == {"1", "2"}
        # A↔B links → at least 1 edge
        assert len(graph["edges"]) >= 1

    def test_graph_preserves_zettel_metadata(self, tmp_path: Path) -> None:
        svc = _build_service(tmp_path, {"1.md": ZETTEL_A})
        exporter = GraphExporter()

        graph = exporter.export(svc.store, [], svc.backlinks)

        node = graph["nodes"][0]
        assert node["id"] == "1"
        assert node["title"] == "Alpha Note"
        assert node["type"] == "permanent"
        assert node["maturity"] == "evergreen"

    def test_graph_sequence_edges(self, tmp_path: Path) -> None:
        svc = _build_service(
            tmp_path,
            {"10.md": ZETTEL_SEQ_ROOT, "11.md": ZETTEL_SEQ_CHILD},
        )
        exporter = GraphExporter()

        graph = exporter.export(svc.store, [], svc.backlinks)

        seq_edges = [e for e in graph["edges"] if e.get("type") == "sequence"]
        assert len(seq_edges) == 1
        assert seq_edges[0]["source"] == "11"
        assert seq_edges[0]["target"] == "10"


class TestPreviewExportChain:
    """ZettelService → PreviewExporter produces preview data."""

    def test_previews_generated(self, tmp_path: Path) -> None:
        svc = _build_service(tmp_path, {"1.md": ZETTEL_A, "2.md": ZETTEL_B})
        exporter = PreviewExporter()

        previews = exporter.export(svc.store)

        assert "1" in previews
        assert "2" in previews
        assert previews["1"]["title"] == "Alpha Note"
        assert previews["2"]["title"] == "Beta Note"
        # Excerpts extracted from body
        assert len(previews["1"]["excerpt"]) > 0
        assert len(previews["2"]["excerpt"]) > 0


class TestSuggestionChain:
    """ZettelService + tags → SuggestionService computes suggestions."""

    def test_suggestions_from_shared_tags(self, tmp_path: Path) -> None:
        # Two unlinked zettels sharing the same tag set → should produce suggestion
        z_x = """\
---
id: 100
date: 2024-01-01
---
# Note X

Content of note X.
"""
        z_y = """\
---
id: 200
date: 2024-01-02
---
# Note Y

Content of note Y.
"""
        svc = _build_service(tmp_path, {"100.md": z_x, "200.md": z_y})
        suggestion_svc = SuggestionService()
        tags_metadata = [
            {"src_path": "100.md", "tags": ["alpha", "beta"]},
            {"src_path": "200.md", "tags": ["alpha", "beta"]},
        ]

        suggestions = suggestion_svc.compute(svc.store, tags_metadata)

        # Perfect tag overlap (Jaccard 1.0) → suggestions in both directions
        assert 100 in suggestions or 200 in suggestions

    def test_no_suggestions_between_linked_zettels(self, tmp_path: Path) -> None:
        z_a = """\
---
id: 100
date: 2024-01-01
---
# Note A

Links to [[200]].
"""
        z_b = """\
---
id: 200
date: 2024-01-02
---
# Note B

Content of note B.
"""
        svc = _build_service(tmp_path, {"100.md": z_a, "200.md": z_b})
        suggestion_svc = SuggestionService()
        tags_metadata = [
            {"src_path": "100.md", "tags": ["alpha", "beta"]},
            {"src_path": "200.md", "tags": ["alpha", "beta"]},
        ]

        suggestions = suggestion_svc.compute(svc.store, tags_metadata)

        # Already linked → should NOT suggest
        target_ids = {s["target_id"] for s in suggestions.get(100, [])}
        assert 200 not in target_ids


# -- Tests: PageTransformer pipeline -----------------------------------------


class TestPageTransformerChain:
    """ZettelService → PageTransformer applies all adapters end-to-end."""

    def test_transform_enriches_zettel_page(self, tmp_path: Path) -> None:
        file_map = {"1.md": ZETTEL_A, "2.md": ZETTEL_B, "3.md": ZETTEL_C}
        svc = _build_service(tmp_path, file_map)
        files, _ = _make_files(tmp_path, file_map)
        config = _make_full_config(tmp_path)

        page = MagicMock()
        page.file.src_path = "1.md"
        page.file.abs_src_path = str(tmp_path / "1.md")
        page.url = "1/"
        page.meta = {}
        page.previous_page = None
        page.next_page = None

        transformer = PageTransformer()
        result_md = transformer.transform(ZETTEL_A, page, config, files, svc)

        assert isinstance(result_md, str)
        assert page.meta["is_zettel"] is True
        assert page.meta["zettel"].id == 1
        assert page.meta["zettel"].title == "Alpha Note"

    def test_transform_non_zettel_page(self, tmp_path: Path) -> None:
        svc = _build_service(tmp_path, {"1.md": ZETTEL_A})
        files, _ = _make_files(tmp_path, {"1.md": ZETTEL_A})
        config = _make_full_config(tmp_path)

        page = MagicMock()
        page.file.src_path = "index.md"
        page.file.abs_src_path = None
        page.url = ""
        page.meta = {}

        transformer = PageTransformer()
        result_md = transformer.transform("# Home", page, config, files, svc)

        assert isinstance(result_md, str)
        assert page.meta["is_zettel"] is False

    def test_backlinks_populated_across_pages(self, tmp_path: Path) -> None:
        # Backlink adapter adds backlinks to TARGET zettels when the SOURCE
        # page is processed. So process zettel 1 (which links to 2) first,
        # then verify zettel 2 gained a backlink.
        file_map = {"1.md": ZETTEL_A, "2.md": ZETTEL_B}
        svc = _build_service(tmp_path, file_map)
        files, _ = _make_files(tmp_path, file_map)
        config = _make_full_config(tmp_path)
        transformer = PageTransformer()

        # Process zettel 1's page (source of link to zettel 2)
        page1 = MagicMock()
        page1.file.src_path = "1.md"
        page1.file.abs_src_path = str(tmp_path / "1.md")
        page1.url = "1/"
        page1.meta = {}
        page1.previous_page = None
        page1.next_page = None
        transformer.transform(ZETTEL_A, page1, config, files, svc)

        # Now zettel 2 (the target) should have gained a backlink
        zettel_2 = svc.get_zettel_by_id(2)
        assert zettel_2 is not None
        assert len(zettel_2.backlinks) > 0

    def test_sequence_data_populated(self, tmp_path: Path) -> None:
        file_map = {
            "10.md": ZETTEL_SEQ_ROOT,
            "11.md": ZETTEL_SEQ_CHILD,
            "12.md": ZETTEL_SEQ_GRANDCHILD,
        }
        svc = _build_service(tmp_path, file_map)
        files, _ = _make_files(tmp_path, file_map)
        config = _make_full_config(tmp_path)

        page = MagicMock()
        page.file.src_path = "11.md"
        page.file.abs_src_path = str(tmp_path / "11.md")
        page.url = "11/"
        page.meta = {}
        page.previous_page = None
        page.next_page = None

        transformer = PageTransformer()
        transformer.transform(ZETTEL_SEQ_CHILD, page, config, files, svc)

        zettel = page.meta["zettel"]
        assert zettel.sequence_parent is not None
        assert len(zettel.sequence_children) > 0
