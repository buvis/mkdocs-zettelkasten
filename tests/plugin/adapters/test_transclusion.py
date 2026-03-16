from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.transclusion import (
    _body_without_refs,
    _extract_section,
    adapt_transclusion,
)
from tests.plugin.conftest import _make_zettel_mock


class TestBodyWithoutRefs:
    def test_returns_body_as_is_when_no_divider(self) -> None:
        assert (
            _body_without_refs("\n# Title\n\nBody text.\n")
            == "\n# Title\n\nBody text.\n"
        )

    def test_strips_reference_footer(self) -> None:
        assert _body_without_refs("\nBody.\n---\nref: foo\n---\n") == "\nBody.\n"

    def test_returns_empty_for_empty_body(self) -> None:
        assert _body_without_refs("") == ""


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


class TestAdaptTransclusion:
    def test_embeds_full_note(self) -> None:
        zettel = _make_zettel_mock(
            0, title="Target", rel_path="target.md", body="\nHello world.\n"
        )
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

    def test_embed_header_links_to_source(self) -> None:
        zettel = _make_zettel_mock(
            0, title="Target", rel_path="target.md", body="\nContent.\n"
        )
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111]]", lookup, site_url="https://example.com/", file_suffix=".md"
        )
        assert '<a href="https://example.com/111/">Target</a>' in result

    def test_alias_overrides_header_text(self) -> None:
        zettel = _make_zettel_mock(
            0, title="Target", rel_path="target.md", body="\nContent.\n"
        )
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111|My Alias]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert "My Alias</a>" in result

    def test_strips_h1_when_configured(self) -> None:
        zettel = _make_zettel_mock(
            0, title="T", rel_path="target.md", body="\n# Title\n\nBody.\n"
        )
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

    def test_keeps_h1_when_strip_disabled(self) -> None:
        zettel = _make_zettel_mock(
            0, title="T", rel_path="target.md", body="\n# Title\n\nBody.\n"
        )
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

    def test_section_embed(self) -> None:
        zettel = _make_zettel_mock(
            0,
            title="T",
            rel_path="target.md",
            body="\n## Intro\n\nFirst.\n\n## Details\n\nSecond.\n",
        )
        lookup = MagicMock(return_value=zettel)

        result = adapt_transclusion(
            "![[111#Intro]]",
            lookup,
            site_url="https://example.com/",
            file_suffix=".md",
        )
        assert "First." in result
        assert "Second." not in result

    def test_section_not_found_renders_warning(self) -> None:
        zettel = _make_zettel_mock(
            0, title="T", rel_path="target.md", body="\n## Intro\n\nText.\n"
        )
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

    def test_circular_embed_renders_warning(self) -> None:
        za = _make_zettel_mock(0, title="A", rel_path="a.md", body="\n![[2]]\n")
        zb = _make_zettel_mock(0, title="B", rel_path="b.md", body="\n![[1]]\n")

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

    def test_recursive_embed(self) -> None:
        zo = _make_zettel_mock(0, title="Outer", rel_path="outer.md", body="\n![[2]]\n")
        zi = _make_zettel_mock(
            0, title="Inner", rel_path="inner.md", body="\nInner content.\n"
        )

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

    def test_custom_max_embed_depth(self) -> None:
        """With max_embed_depth=1, a 3-level chain should only resolve 1 level deep."""
        z1 = _make_zettel_mock(0, title="Z1", rel_path="z1.md", body="\n![[2]]\n")
        z2 = _make_zettel_mock(0, title="Z2", rel_path="z2.md", body="\n![[3]]\n")
        z3 = _make_zettel_mock(0, title="Z3", rel_path="z3.md", body="\nLeaf.\n")

        def lookup(path: str):
            if "1" in path:
                return z1
            if "2" in path:
                return z2
            if "3" in path:
                return z3
            return None

        result = adapt_transclusion(
            "![[1]]", lookup, site_url="https://example.com/", file_suffix=".md",
            max_embed_depth=1,
        )
        assert "Z2" in result
        assert "Leaf." not in result

    def test_max_embed_depth_stops_recursion(self) -> None:
        # Create a chain of default max_embed_depth (5) + 2 zettels
        chain_len = 5 + 2
        zettels = {}
        for i in range(1, chain_len + 1):
            body = f"\n![[{i + 1}]]\n" if i < chain_len else "\nLeaf content.\n"
            zettels[i] = _make_zettel_mock(
                0, title=f"Z{i}", rel_path=f"z{i}.md", body=body
            )

        def lookup(path: str):
            for zid, z in zettels.items():
                if str(zid) in path:
                    return z
            return None

        result = adapt_transclusion(
            "![[1]]", lookup, site_url="https://example.com/", file_suffix=".md"
        )
        # Leaf content should NOT appear because chain exceeds max depth
        assert "Leaf content." not in result
