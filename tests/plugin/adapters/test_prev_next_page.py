from unittest.mock import MagicMock

from mkdocs.structure.files import File

from mkdocs_zettelkasten.plugin.adapters.prev_next_page import get_prev_next_page


def _make_file(src_path: str, abs_src_path: str | None = None) -> MagicMock:
    f = MagicMock(spec=File)
    f.src_path = src_path
    f.abs_src_path = abs_src_path or f"/docs/{src_path}"
    f.page = MagicMock()
    return f


def _make_zettel(zettel_id: int, path: str) -> MagicMock:
    z = MagicMock()
    z.id = zettel_id
    z.path = path
    return z


def _make_page(src_path: str, is_zettel: bool = True, zettel_id: int = 1) -> MagicMock:
    page = MagicMock()
    page.file.src_path = src_path
    page.meta = {"is_zettel": is_zettel}
    if is_zettel:
        zettel = MagicMock()
        zettel.id = zettel_id
        page.meta["zettel"] = zettel
    return page


class TestGetPrevNextPage:
    def test_index_page_returns_first_zettel(self) -> None:
        page = _make_page("index.md", is_zettel=False)
        z = _make_zettel(1, "/docs/note.md")
        f = _make_file("note.md", "/docs/note.md")
        files = MagicMock()
        files.__iter__ = lambda self: iter([f])

        _, next_page = get_prev_next_page(page, files, [z])
        assert next_page is not None

    def test_tags_page_returns_none(self) -> None:
        page = _make_page("tags.md", is_zettel=False)
        files = MagicMock()
        files.__iter__ = lambda self: iter([])

        prev, next_p = get_prev_next_page(page, files, [])
        assert prev is None
        assert next_p is None

    def test_non_zettel_returns_none(self) -> None:
        page = _make_page("about.md", is_zettel=False)
        files = MagicMock()
        files.__iter__ = lambda self: iter([])

        prev, next_p = get_prev_next_page(page, files, [])
        assert prev is None
        assert next_p is None

    def test_zettel_navigation(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md")
        z2 = _make_zettel(2, "/docs/b.md")
        z3 = _make_zettel(3, "/docs/c.md")

        f_index = _make_file("index.md")
        f1 = _make_file("a.md", "/docs/a.md")
        f2 = _make_file("b.md", "/docs/b.md")
        f3 = _make_file("c.md", "/docs/c.md")

        files = MagicMock()
        files.__iter__ = lambda self: iter([f_index, f1, f2, f3])

        page = _make_page("b.md", zettel_id=2)

        prev, next_p = get_prev_next_page(page, files, [z1, z2, z3])
        assert prev is f1.page
        assert next_p is f3.page

    def test_first_zettel_has_homepage_as_prev(self) -> None:
        z1 = _make_zettel(1, "/docs/a.md")
        z2 = _make_zettel(2, "/docs/b.md")

        f_index = _make_file("index.md")
        f1 = _make_file("a.md", "/docs/a.md")
        f2 = _make_file("b.md", "/docs/b.md")

        files = MagicMock()
        files.__iter__ = lambda self: iter([f_index, f1, f2])

        page = _make_page("a.md", zettel_id=1)

        prev, next_p = get_prev_next_page(page, files, [z1, z2])
        assert prev is f_index.page
        assert next_p is f2.page
