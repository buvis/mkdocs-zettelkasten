from mkdocs_zettelkasten.plugin.services.outline_service import OutlineService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


def _make_zettel(
    zettel_id,
    title,
    rel_path,
    note_type=None,
    maturity=None,
    links=None,
    role=None,
    body="",
    sequence_parent_id=None,
):
    return _make_zettel_mock(
        zettel_id,
        title=title,
        rel_path=rel_path,
        note_type=note_type,
        maturity=maturity,
        links=links,
        role=role,
        body=body,
        sequence_parent_id=sequence_parent_id,
    )


class TestMocOutlines:
    def setup_method(self):
        self.service = OutlineService()

    def test_moc_entries_in_document_order(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["b.md", "a.md"])
        a = _make_zettel(10, "A", "a.md")
        b = _make_zettel(20, "B", "b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert [e["title"] for e in entries] == ["B", "A"]

    def test_preview_text(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md"])
        a = _make_zettel(10, "A", "a.md", body="First sentence here. More text.")
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert "First sentence" in result["moc_outlines"][0]["entries"][0]["preview"]

    def test_entry_metadata(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md"])
        a = _make_zettel(10, "A", "a.md", note_type="permanent", maturity="evergreen")
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        entry = result["moc_outlines"][0]["entries"][0]
        assert entry["note_type"] == "permanent"
        assert entry["maturity"] == "evergreen"

    def test_skips_unresolvable_links(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["missing.md", "a.md"])
        a = _make_zettel(10, "A", "a.md")
        store = ZettelStore([moc, a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert len(result["moc_outlines"][0]["entries"]) == 1

    def test_no_moc_outlines_when_no_mocs(self):
        a = _make_zettel(10, "A", "a.md")
        store = ZettelStore([a])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert result["moc_outlines"] == []

    def test_moc_with_no_resolvable_links_excluded(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["missing.md"])
        store = ZettelStore([moc])
        result = self.service.compute(store, {}, file_suffix=".md")
        assert result["moc_outlines"] == []


class TestGapDetection:
    def setup_method(self):
        self.service = OutlineService()

    def test_gap_when_no_mutual_links(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md", "b.md"])
        a = _make_zettel(10, "A", "a.md")
        b = _make_zettel(20, "B", "b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[0]["gap_before"] is False
        assert entries[1]["gap_before"] is True

    def test_no_gap_when_linked(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md", "b.md"])
        a = _make_zettel(10, "A", "a.md", links=["b.md"])
        b = _make_zettel(20, "B", "b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[1]["gap_before"] is False

    def test_no_gap_when_reverse_linked(self):
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md", "b.md"])
        a = _make_zettel(10, "A", "a.md")
        b = _make_zettel(20, "B", "b.md", links=["a.md"])
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        entries = result["moc_outlines"][0]["entries"]
        assert entries[1]["gap_before"] is False


class TestSequenceOutlines:
    def setup_method(self):
        self.service = OutlineService()

    def test_builds_tree_from_root(self):
        root = _make_zettel(1, "Root", "r.md")
        child = _make_zettel(2, "Child", "c.md", sequence_parent_id=1)
        store = ZettelStore([root, child])
        seq_children = {1: [2]}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        tree = result["sequence_outlines"]
        assert len(tree) == 1
        assert tree[0]["title"] == "Root"
        assert tree[0]["children"][0]["title"] == "Child"

    def test_nested_children(self):
        root = _make_zettel(1, "Root", "r.md")
        child = _make_zettel(2, "Child", "c.md", sequence_parent_id=1)
        grandchild = _make_zettel(3, "Grand", "g.md", sequence_parent_id=2)
        store = ZettelStore([root, child, grandchild])
        seq_children = {1: [2], 2: [3]}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        gc = result["sequence_outlines"][0]["children"][0]["children"]
        assert gc[0]["title"] == "Grand"

    def test_excludes_non_root(self):
        child = _make_zettel(2, "Child", "c.md", sequence_parent_id=1)
        store = ZettelStore([child])
        seq_children = {}
        result = self.service.compute(store, seq_children, file_suffix=".md")
        assert result["sequence_outlines"] == []


class TestFlattenTree:
    def setup_method(self):
        self.service = OutlineService()

    def test_flattens_nested_tree(self):
        root = _make_zettel(1, "Root", "r.md")
        child = _make_zettel(2, "Child", "c.md", sequence_parent_id=1)
        grandchild = _make_zettel(3, "Grand", "g.md", sequence_parent_id=2)
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
        moc = _make_zettel(1, "MOC", "moc.md", role="moc", links=["a.md", "b.md"])
        a = _make_zettel(10, "A", "a.md")
        b = _make_zettel(20, "B", "b.md")
        store = ZettelStore([moc, a, b])
        result = self.service.compute(store, {}, file_suffix=".md")
        text = result["moc_outlines"][0]["transclusion_text"]
        assert "![[10|A]]" in text
        assert "![[20|B]]" in text
