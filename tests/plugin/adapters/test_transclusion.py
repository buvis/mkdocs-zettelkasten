from pathlib import Path
from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.transclusion import (
    _extract_section,
    _read_zettel_body,
    adapt_transclusion,
)


class TestReadZettelBody:
    def test_strips_yaml_frontmatter(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\ntitle: Test\n---\n\n# Title\n\nBody text.\n")
        assert _read_zettel_body(f) == "\n# Title\n\nBody text.\n"

    def test_strips_reference_footer(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\n---\n\nBody.\n---\nref: foo\n---\n")
        assert _read_zettel_body(f) == "\nBody.\n"

    def test_returns_empty_for_header_only(self, tmp_path: Path) -> None:
        f = tmp_path / "note.md"
        f.write_text("---\nid: 123\n---\n")
        assert _read_zettel_body(f) == ""


class TestExtractSection:
    def test_extracts_h2_section(self) -> None:
        body = "## Intro\n\nFirst.\n\n## Details\n\nSecond.\n"
        assert _extract_section(body, "Intro") == "## Intro\n\nFirst.\n\n"

    def test_extracts_last_section(self) -> None:
        body = "## Intro\n\nFirst.\n\n## Details\n\nSecond.\n"
        assert _extract_section(body, "Details") == "## Details\n\nSecond.\n"

    def test_case_insensitive_match(self) -> None:
        body = "## My Section\n\nContent.\n"
        assert _extract_section(body, "my section") == "## My Section\n\nContent.\n"

    def test_stops_at_same_level_heading(self) -> None:
        body = "## A\n\nText.\n\n### Sub\n\nDeep.\n\n## B\n\nOther.\n"
        result = _extract_section(body, "A")
        assert "### Sub" in result
        assert "## B" not in result

    def test_returns_none_when_not_found(self) -> None:
        body = "## Intro\n\nText.\n"
        assert _extract_section(body, "Nonexistent") is None


def _make_zettel(title: str, path: Path, url: str = "/note/") -> MagicMock:
    z = MagicMock()
    z.title = title
    z.path = path
    z.rel_path = str(path.name)
    return z


class TestAdaptTransclusion:
    def test_embeds_full_note(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: Target\n---\n\nHello world.\n")
        zettel = _make_zettel("Target", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "before\n\n![[111]]\n\nafter",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert "Hello world." in result
        assert '<div class="zettel-embed">' in result
        assert "before" in result
        assert "after" in result

    def test_embed_header_links_to_source(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: Target\n---\n\nContent.\n")
        zettel = _make_zettel("Target", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111]]", lookup, site_url="https://example.com/", file_suffix=".md"
        )
        assert '<a href="https://example.com/111/">Target</a>' in result

    def test_alias_overrides_header_text(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: Target\n---\n\nContent.\n")
        zettel = _make_zettel("Target", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111|My Alias]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert "My Alias</a>" in result

    def test_strips_h1_when_configured(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: T\n---\n\n# Title\n\nBody.\n")
        zettel = _make_zettel("T", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
            strip_heading=True,
        )
        assert "# Title" not in result
        assert "Body." in result

    def test_keeps_h1_when_strip_disabled(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: T\n---\n\n# Title\n\nBody.\n")
        zettel = _make_zettel("T", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
            strip_heading=False,
        )
        assert "# Title" in result

    def test_not_found_renders_warning(self) -> None:
        lookup = MagicMock(return_value=None)
        result = adapt_transclusion(
            "![[nonexistent]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert 'warning "Embed not found"' in result
        assert "nonexistent" in result

    def test_section_embed(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text(
            "---\nid: 111\ntitle: T\n---\n\n## Intro\n\nFirst.\n\n## Details\n\nSecond.\n"
        )
        zettel = _make_zettel("T", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111#Intro]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert "First." in result
        assert "Second." not in result

    def test_section_not_found_renders_warning(self, tmp_path: Path) -> None:
        target = tmp_path / "target.md"
        target.write_text("---\nid: 111\ntitle: T\n---\n\n## Intro\n\nText.\n")
        zettel = _make_zettel("T", target)
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111#Missing]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert 'warning "Section not found"' in result

    def test_skips_embeds_in_code_blocks(self) -> None:
        lookup = MagicMock()
        md = "text\n```\n![[111]]\n```\nafter"
        result = adapt_transclusion(
            md, lookup, site_url="https://example.com/", file_suffix=".md"
        )
        assert "![[111]]" in result
        lookup.assert_not_called()

    def test_circular_embed_renders_warning(self, tmp_path: Path) -> None:
        a = tmp_path / "a.md"
        a.write_text("---\nid: 1\ntitle: A\n---\n\n![[2]]\n")
        b = tmp_path / "b.md"
        b.write_text("---\nid: 2\ntitle: B\n---\n\n![[1]]\n")
        za = _make_zettel("A", a)
        zb = _make_zettel("B", b)

        def lookup(path: str):
            if "1" in path:
                return za
            if "2" in path:
                return zb
            return None

        result = adapt_transclusion(
            "![[1]]", lookup, site_url="https://example.com/", file_suffix=".md"
        )
        assert 'warning "Circular embed"' in result

    def test_recursive_embed(self, tmp_path: Path) -> None:
        inner = tmp_path / "inner.md"
        inner.write_text("---\nid: 2\ntitle: Inner\n---\n\nInner content.\n")
        outer = tmp_path / "outer.md"
        outer.write_text("---\nid: 1\ntitle: Outer\n---\n\n![[2]]\n")
        zo = _make_zettel("Outer", outer)
        zi = _make_zettel("Inner", inner)

        def lookup(path: str):
            if "1" in path:
                return zo
            if "2" in path:
                return zi
            return None

        result = adapt_transclusion(
            "![[1]]", lookup, site_url="https://example.com/", file_suffix=".md"
        )
        assert "Inner content." in result
