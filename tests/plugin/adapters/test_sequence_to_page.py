from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.sequence_to_page import (
    adapt_sequence_to_page,
)
from tests.plugin.conftest import _make_zettel_mock


def _make_zettel_obj(
    zettel_id: int,
    title: str,
    rel_path: str,
    sequence_parent_id: int | None = None,
):
    return _make_zettel_mock(
        zettel_id, title=title, rel_path=rel_path,
        sequence_parent_id=sequence_parent_id,
    )


def _make_page(zettel: MagicMock | None) -> MagicMock:
    page = MagicMock()
    if zettel:
        page.meta = {"is_zettel": True, "zettel": zettel}
    else:
        page.meta = {"is_zettel": False}
    return page


class TestAdaptSequenceToPage:
    def test_non_zettel_skipped(self) -> None:
        page = _make_page(None)
        adapt_sequence_to_page(page, {}, lambda _zid: None)

    def test_parent_populated(self) -> None:
        parent = _make_zettel_obj(1, "Parent", "parent.md")
        child = _make_zettel_obj(2, "Child", "child.md", sequence_parent_id=1)
        page = _make_page(child)
        adapt_sequence_to_page(page, {}, lambda zid: parent if zid == 1 else None)
        assert child.sequence_parent == {"url": "parent/", "title": "Parent"}

    def test_parent_not_found(self) -> None:
        child = _make_zettel_obj(2, "Child", "child.md", sequence_parent_id=999)
        page = _make_page(child)
        adapt_sequence_to_page(page, {}, lambda _zid: None)
        assert child.sequence_parent is None

    def test_children_populated(self) -> None:
        parent = _make_zettel_obj(1, "Parent", "parent.md")
        child_a = _make_zettel_obj(2, "A", "a.md")
        child_b = _make_zettel_obj(3, "B", "b.md")
        page = _make_page(parent)
        lookup = {2: child_a, 3: child_b}
        adapt_sequence_to_page(page, {1: [2, 3]}, lookup.get)
        assert parent.sequence_children == [
            {"url": "a/", "title": "A"},
            {"url": "b/", "title": "B"},
        ]

    def test_no_children(self) -> None:
        leaf = _make_zettel_obj(3, "Leaf", "leaf.md", sequence_parent_id=2)
        page = _make_page(leaf)
        adapt_sequence_to_page(page, {}, lambda _zid: None)
        assert leaf.sequence_children == []

    def test_breadcrumb_chain(self) -> None:
        root = _make_zettel_obj(1, "Root", "root.md")
        mid = _make_zettel_obj(2, "Mid", "mid.md", sequence_parent_id=1)
        leaf = _make_zettel_obj(3, "Leaf", "leaf.md", sequence_parent_id=2)
        page = _make_page(leaf)
        lookup = {1: root, 2: mid, 3: leaf}
        adapt_sequence_to_page(page, {}, lookup.get)
        assert leaf.sequence_breadcrumb == [
            {"url": "root/", "title": "Root"},
            {"url": "mid/", "title": "Mid"},
        ]

    def test_breadcrumb_single_parent(self) -> None:
        parent = _make_zettel_obj(1, "Parent", "parent.md")
        child = _make_zettel_obj(2, "Child", "child.md", sequence_parent_id=1)
        page = _make_page(child)
        adapt_sequence_to_page(page, {}, lambda zid: parent if zid == 1 else None)
        assert child.sequence_breadcrumb == [{"url": "parent/", "title": "Parent"}]

    def test_breadcrumb_handles_cycle(self) -> None:
        z1 = _make_zettel_obj(1, "A", "a.md", sequence_parent_id=2)
        z2 = _make_zettel_obj(2, "B", "b.md", sequence_parent_id=1)
        page = _make_page(z1)
        lookup = {1: z1, 2: z2}
        adapt_sequence_to_page(page, {}, lookup.get)
        assert len(z1.sequence_breadcrumb) <= 2

    def test_custom_file_suffix(self) -> None:
        parent = _make_zettel_obj(1, "Parent", "parent.txt")
        child = _make_zettel_obj(2, "Child", "child.txt", sequence_parent_id=1)
        page = _make_page(child)
        adapt_sequence_to_page(
            page, {}, lambda zid: parent if zid == 1 else None, file_suffix=".txt"
        )
        assert child.sequence_parent == {"url": "parent/", "title": "Parent"}


class TestSequenceTree:
    def test_tree_built_for_root(self) -> None:
        root = _make_zettel_obj(1, "Root", "root.md")
        root.sequence_tree = []
        child = _make_zettel_obj(2, "Child", "child.md", sequence_parent_id=1)
        child.sequence_tree = []
        page = _make_page(root)
        lookup = {1: root, 2: child}
        adapt_sequence_to_page(page, {1: [2]}, lookup.get)
        assert len(root.sequence_tree) == 1
        tree = root.sequence_tree[0]
        assert tree["title"] == "Root"
        assert tree["current"] is True
        assert len(tree["children"]) == 1
        assert tree["children"][0]["title"] == "Child"

    def test_tree_built_for_leaf(self) -> None:
        root = _make_zettel_obj(1, "Root", "root.md")
        root.sequence_tree = []
        mid = _make_zettel_obj(2, "Mid", "mid.md", sequence_parent_id=1)
        mid.sequence_tree = []
        leaf = _make_zettel_obj(3, "Leaf", "leaf.md", sequence_parent_id=2)
        leaf.sequence_tree = []
        page = _make_page(leaf)
        lookup = {1: root, 2: mid, 3: leaf}
        adapt_sequence_to_page(page, {1: [2], 2: [3]}, lookup.get)
        assert len(leaf.sequence_tree) == 1
        tree = leaf.sequence_tree[0]
        assert tree["title"] == "Root"
        assert tree["current"] is False
        mid_node = tree["children"][0]
        assert mid_node["title"] == "Mid"
        leaf_node = mid_node["children"][0]
        assert leaf_node["title"] == "Leaf"
        assert leaf_node["current"] is True

    def test_tree_empty_when_not_in_sequence(self) -> None:
        standalone = _make_zettel_obj(1, "Alone", "alone.md")
        standalone.sequence_tree = []
        page = _make_page(standalone)
        adapt_sequence_to_page(page, {}, lambda _zid: None)
        assert standalone.sequence_tree == []

    def test_tree_shows_branches(self) -> None:
        root = _make_zettel_obj(1, "Root", "root.md")
        root.sequence_tree = []
        a = _make_zettel_obj(2, "A", "a.md", sequence_parent_id=1)
        a.sequence_tree = []
        b = _make_zettel_obj(3, "B", "b.md", sequence_parent_id=1)
        b.sequence_tree = []
        page = _make_page(a)
        lookup = {1: root, 2: a, 3: b}
        adapt_sequence_to_page(page, {1: [2, 3]}, lookup.get)
        tree = a.sequence_tree[0]
        assert len(tree["children"]) == 2
        titles = [c["title"] for c in tree["children"]]
        assert "A" in titles
        assert "B" in titles
