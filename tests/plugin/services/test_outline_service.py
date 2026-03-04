from pathlib import Path
from unittest.mock import MagicMock

import pytest
from mkdocs.structure.files import Files

from mkdocs_zettelkasten.plugin.services.outline_service import OutlineService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


class TestConfigure:
    def test_sets_output_folder_and_site_dir(self):
        svc = OutlineService()
        folder = Path("/tmp/outline")
        svc.configure(folder, "/tmp/site")
        assert svc.output_folder == folder
        assert svc._site_dir == "/tmp/site"

    def test_overwrites_previous_config(self):
        svc = OutlineService()
        svc.configure(Path("/old"), "/old-site")
        svc.configure(Path("/new"), "/new-site")
        assert svc.output_folder == Path("/new")
        assert svc._site_dir == "/new-site"


class TestGenerate:
    def test_raises_before_configure(self):
        svc = OutlineService()
        with pytest.raises(RuntimeError, match="configure"):
            svc.generate({"moc_outlines": [], "sequence_outlines": []})

    def test_writes_outline_file(self, tmp_path):
        svc = OutlineService()
        svc.configure(tmp_path, str(tmp_path))
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md"]
        )
        a = _make_zettel_mock(
            10, title="A", rel_path="a.md", body="Preview text here."
        )
        store = ZettelStore([moc, a])
        outlines = svc.compute(store, {}, file_suffix=".md")
        svc.generate(outlines)
        output = (tmp_path / "outline.md").read_text()
        assert "# Outlines" in output
        assert "MOC" in output
        assert "[A]" in output

    def test_renders_sequence_outlines(self, tmp_path):
        svc = OutlineService()
        svc.configure(tmp_path, str(tmp_path))
        root = _make_zettel_mock(1, title="Root", rel_path="r.md")
        child = _make_zettel_mock(
            2, title="Child", rel_path="c.md", sequence_parent_id=1
        )
        store = ZettelStore([root, child])
        outlines = svc.compute(store, {1: [2]}, file_suffix=".md")
        svc.generate(outlines)
        output = (tmp_path / "outline.md").read_text()
        assert "Sequence: Root" in output
        assert "[Child]" in output


class TestAddToBuild:
    def test_raises_before_configure(self):
        svc = OutlineService()
        files = MagicMock(spec=Files)
        with pytest.raises(RuntimeError, match="configure"):
            svc.add_to_build(files)

    def test_appends_outline_file(self, tmp_path):
        svc = OutlineService()
        svc.configure(tmp_path, str(tmp_path))
        files = Files([])
        svc.add_to_build(files)
        paths = [f.src_path for f in files]
        assert "outline.md" in paths

    def test_file_points_to_configured_dirs(self, tmp_path):
        svc = OutlineService()
        site_dir = str(tmp_path / "site")
        src_dir = tmp_path / "src"
        svc.configure(src_dir, site_dir)
        files = Files([])
        svc.add_to_build(files)
        added = next(iter(files))
        assert added.abs_src_path == str(src_dir / "outline.md")
        assert added.abs_dest_path.startswith(site_dir)


class TestMocOutlines:
    def setup_method(self):
        self.service = OutlineService()

    def test_moc_entries_in_document_order(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["b.md", "a.md"]
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        b = _make_zettel_mock(20, title="B", rel_path="b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert [e["title"] for e in entries] == ["B", "A"]

    def test_preview_text(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md"]
        )
        a = _make_zettel_mock(
            10, title="A", rel_path="a.md", body="First sentence here. More text."
        )
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert "First sentence" in result["moc_outlines"][0]["entries"][0]["preview"]

    def test_entry_metadata(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md"]
        )
        a = _make_zettel_mock(
            10,
            title="A",
            rel_path="a.md",
            note_type="permanent",
            maturity="evergreen",
        )
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        entry = result["moc_outlines"][0]["entries"][0]
        assert entry["note_type"] == "permanent"
        assert entry["maturity"] == "evergreen"

    def test_skips_unresolvable_links(self):
        moc = _make_zettel_mock(
            1,
            title="MOC",
            rel_path="moc.md",
            role="moc",
            links=["missing.md", "a.md"],
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert len(result["moc_outlines"][0]["entries"]) == 1

    def test_no_moc_outlines_when_no_mocs(self):
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        store = ZettelStore([a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert result["moc_outlines"] == []

    def test_moc_with_no_resolvable_links_excluded(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["missing.md"]
        )
        store = ZettelStore([moc])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert result["moc_outlines"] == []


class TestGapDetection:
    def setup_method(self):
        self.service = OutlineService()

    def test_gap_when_no_mutual_links(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md", "b.md"]
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        b = _make_zettel_mock(20, title="B", rel_path="b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[0]["gap_before"] is False
        assert entries[1]["gap_before"] is True

    def test_no_gap_when_linked(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md", "b.md"]
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md", links=["b.md"])
        b = _make_zettel_mock(20, title="B", rel_path="b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[1]["gap_before"] is False

    def test_no_gap_when_reverse_linked(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md", "b.md"]
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        b = _make_zettel_mock(20, title="B", rel_path="b.md", links=["a.md"])
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[1]["gap_before"] is False


class TestSequenceOutlines:
    def setup_method(self):
        self.service = OutlineService()

    def test_builds_tree_from_root(self):
        root = _make_zettel_mock(1, title="Root", rel_path="r.md")
        child = _make_zettel_mock(
            2, title="Child", rel_path="c.md", sequence_parent_id=1
        )
        store = ZettelStore([root, child])
        seq_children = {1: [2]}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        tree = result["sequence_outlines"]
        assert len(tree) == 1
        assert tree[0]["title"] == "Root"
        assert tree[0]["children"][0]["title"] == "Child"

    def test_nested_children(self):
        root = _make_zettel_mock(1, title="Root", rel_path="r.md")
        child = _make_zettel_mock(
            2, title="Child", rel_path="c.md", sequence_parent_id=1
        )
        grandchild = _make_zettel_mock(
            3, title="Grand", rel_path="g.md", sequence_parent_id=2
        )
        store = ZettelStore([root, child, grandchild])
        seq_children = {1: [2], 2: [3]}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        gc = result["sequence_outlines"][0]["children"][0]["children"]
        assert gc[0]["title"] == "Grand"

    def test_excludes_non_root(self):
        child = _make_zettel_mock(
            2, title="Child", rel_path="c.md", sequence_parent_id=1
        )
        store = ZettelStore([child])
        seq_children = {}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        assert result["sequence_outlines"] == []


class TestFlattenTree:
    def setup_method(self):
        self.service = OutlineService()

    def test_flattens_nested_tree(self):
        root = _make_zettel_mock(1, title="Root", rel_path="r.md")
        child = _make_zettel_mock(
            2, title="Child", rel_path="c.md", sequence_parent_id=1
        )
        grandchild = _make_zettel_mock(
            3, title="Grand", rel_path="g.md", sequence_parent_id=2
        )
        store = ZettelStore([root, child, grandchild])
        seq_children = {1: [2], 2: [3]}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        flat = result["sequence_outlines"][0]["flat_entries"]
        assert len(flat) == 3
        assert flat[0]["indent"] == 0
        assert flat[1]["indent"] == 1
        assert flat[2]["indent"] == 2


class TestTransclusionText:
    def setup_method(self):
        self.service = OutlineService()

    def test_moc_transclusion_text(self):
        moc = _make_zettel_mock(
            1, title="MOC", rel_path="moc.md", role="moc", links=["a.md", "b.md"]
        )
        a = _make_zettel_mock(10, title="A", rel_path="a.md")
        b = _make_zettel_mock(20, title="B", rel_path="b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        text = result["moc_outlines"][0]["transclusion_text"]
        assert "![[10|A]]" in text
        assert "![[20|B]]" in text
