from pathlib import Path

from mkdocs_zettelkasten.plugin.services.link_resolver import LinkResolver
from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore
from tests.plugin.conftest import _make_zettel_mock


class TestLinkResolver:
    def test_empty_store(self) -> None:
        store = ZettelStore()
        result = LinkResolver.resolve(store)
        assert result.resolved == {}
        assert result.broken == []

    def test_basic_resolution(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b.md"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == {2}
        assert result.resolved[2] == set()
        assert result.broken == []

    def test_broken_links_collected(self) -> None:
        z1 = _make_zettel_mock(
            1, path=Path("/docs/a.md"), rel_path="a.md", links=["missing"]
        )
        store = ZettelStore([z1])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == set()
        assert result.broken == [("a.md", "missing")]

    def test_self_links_included(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["a.md"])
        store = ZettelStore([z1])

        result = LinkResolver.resolve(store)

        assert 1 in result.resolved[1]

    def test_multiple_links_to_same_target_deduplicated(self) -> None:
        z1 = _make_zettel_mock(
            1, path=Path("/docs/a.md"), links=["b.md", "b"]
        )
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == {2}

    def test_external_links_skipped(self) -> None:
        z1 = _make_zettel_mock(
            1,
            path=Path("/docs/a.md"),
            links=["http://example.com", "https://example.com", "#anchor", "mailto:x@y"],
        )
        store = ZettelStore([z1])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == set()
        assert result.broken == []

    def test_non_default_file_suffix(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.txt"), links=["b.txt"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.txt"))
        store = ZettelStore([z1, z2])

        result = LinkResolver.resolve(store, file_suffix=".txt")

        assert result.resolved[1] == {2}

    def test_link_without_suffix_resolves(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == {2}

    def test_multiple_sources_multiple_targets(self) -> None:
        z1 = _make_zettel_mock(1, path=Path("/docs/a.md"), links=["b.md", "c.md"])
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"), links=["c.md"])
        z3 = _make_zettel_mock(3, path=Path("/docs/c.md"))
        store = ZettelStore([z1, z2, z3])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == {2, 3}
        assert result.resolved[2] == {3}
        assert result.resolved[3] == set()

    def test_mixed_resolved_and_broken(self) -> None:
        z1 = _make_zettel_mock(
            1, path=Path("/docs/a.md"), rel_path="a.md", links=["b.md", "missing"]
        )
        z2 = _make_zettel_mock(2, path=Path("/docs/b.md"))
        store = ZettelStore([z1, z2])

        result = LinkResolver.resolve(store)

        assert result.resolved[1] == {2}
        assert result.broken == [("a.md", "missing")]
