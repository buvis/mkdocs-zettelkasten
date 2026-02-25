from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.sequence_service import SequenceService
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(zettel_id: int, sequence_parent_id: int | None = None) -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = Path(f"/docs/{zettel_id}.md")
    z.rel_path = f"{zettel_id}.md"
    z.sequence_parent_id = sequence_parent_id
    z.__hash__ = lambda self: hash(zettel_id)
    z.__eq__ = lambda self, other: getattr(other, "id", None) == zettel_id
    return z


class TestSequenceService:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = SequenceService.build_tree(store)
        assert result == {}

    def test_no_sequences(self) -> None:
        z1 = _make_zettel(1)
        z2 = _make_zettel(2)
        store = ZettelStore([z1, z2])
        result = SequenceService.build_tree(store)
        assert result == {}

    def test_single_parent_child(self) -> None:
        parent = _make_zettel(1)
        child = _make_zettel(2, sequence_parent_id=1)
        store = ZettelStore([parent, child])
        result = SequenceService.build_tree(store)
        assert result == {1: [2]}

    def test_multiple_children_sorted_by_id(self) -> None:
        parent = _make_zettel(1)
        child_b = _make_zettel(3, sequence_parent_id=1)
        child_a = _make_zettel(2, sequence_parent_id=1)
        store = ZettelStore([parent, child_a, child_b])
        result = SequenceService.build_tree(store)
        assert result[1] == [2, 3]

    def test_chain(self) -> None:
        z1 = _make_zettel(1)
        z2 = _make_zettel(2, sequence_parent_id=1)
        z3 = _make_zettel(3, sequence_parent_id=2)
        store = ZettelStore([z1, z2, z3])
        result = SequenceService.build_tree(store)
        assert result == {1: [2], 2: [3]}

    def test_branching(self) -> None:
        root = _make_zettel(1)
        branch_a = _make_zettel(2, sequence_parent_id=1)
        branch_b = _make_zettel(3, sequence_parent_id=1)
        leaf = _make_zettel(4, sequence_parent_id=2)
        store = ZettelStore([root, branch_a, branch_b, leaf])
        result = SequenceService.build_tree(store)
        assert result[1] == [2, 3]
        assert result[2] == [4]
        assert 3 not in result
