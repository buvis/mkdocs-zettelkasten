from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


def _make_zettel(zettel_id: int, path: str = "/docs/note.md") -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = Path(path)
    z.__hash__ = lambda self: hash(zettel_id)
    z.__eq__ = lambda self, other: getattr(other, "id", None) == zettel_id
    return z


class TestZettelStore:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        assert store.zettels == []

    def test_update_sorts_by_id(self) -> None:
        z1 = _make_zettel(3, "/docs/c.md")
        z2 = _make_zettel(1, "/docs/a.md")
        z3 = _make_zettel(2, "/docs/b.md")

        store = ZettelStore([z1, z2, z3])
        ids = [z.id for z in store.zettels]
        assert ids == [1, 2, 3]

    def test_deduplicates_by_id(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md")
        z2 = _make_zettel(1, "/docs/a.md")

        store = ZettelStore([z1, z2])
        assert len(store.zettels) == 1

    def test_get_by_path(self) -> None:
        z = _make_zettel(1, "/docs/note.md")
        store = ZettelStore([z])

        assert store.get_by_path(Path("/docs/note.md")) is z
        assert store.get_by_path(Path("/docs/other.md")) is None

    def test_get_by_partial_path(self) -> None:
        z = _make_zettel(1, "/docs/sub/note.md")
        store = ZettelStore([z])

        assert store.get_by_partial_path("note.md") is z
        assert store.get_by_partial_path("nonexistent.md") is None

    def test_partial_path_no_substring_match(self) -> None:
        z = _make_zettel(1, "/docs/foobar.md")
        store = ZettelStore([z])

        assert store.get_by_partial_path("foo.md") is None

    def test_partial_path_exact_stem_match(self) -> None:
        z = _make_zettel(1, "/docs/foo.md")
        store = ZettelStore([z])

        assert store.get_by_partial_path("foo.md") is z
        assert store.get_by_partial_path("foo") is z

    def test_partial_path_dir_segment_match(self) -> None:
        z = _make_zettel(1, "/docs/dir/foo.md")
        store = ZettelStore([z])

        assert store.get_by_partial_path("dir/foo") is z
        assert store.get_by_partial_path("dir/foo.md") is z
        assert store.get_by_partial_path("foo") is z

    def test_partial_path_rejects_wrong_dir(self) -> None:
        z = _make_zettel(1, "/docs/other/foo.md")
        store = ZettelStore([z])

        assert store.get_by_partial_path("dir/foo.md") is None
