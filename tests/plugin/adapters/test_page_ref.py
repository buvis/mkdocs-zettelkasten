from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.page_ref import (
    count_dividers_outside_code_blocks,
    get_page_ref,
)


class TestCountDividersOutsideCodeBlocks:
    def test_no_dividers(self) -> None:
        assert count_dividers_outside_code_blocks(["line1", "line2"]) == 0

    def test_counts_dividers(self) -> None:
        lines = ["---", "content", "---", "more"]
        assert count_dividers_outside_code_blocks(lines) == 2

    def test_ignores_dividers_in_code_blocks(self) -> None:
        lines = ["```", "---", "```", "---"]
        assert count_dividers_outside_code_blocks(lines) == 1

    def test_multiple_code_blocks(self) -> None:
        lines = ["```", "---", "```", "text", "```", "---", "```"]
        assert count_dividers_outside_code_blocks(lines) == 0


class TestGetPageRef:
    def _make_page(self, is_zettel: bool = True) -> MagicMock:
        page = MagicMock()
        page.meta = {"is_zettel": is_zettel}
        page.file.src_path = "test.md"
        return page

    def _make_config(self) -> MagicMock:
        config = MagicMock()
        config.__getitem__ = lambda self, key: {
            "markdown_extensions": [],
            "mdx_configs": {},
        }[key]
        return config

    def test_non_zettel_returns_unchanged(self) -> None:
        page = self._make_page(is_zettel=False)
        md, ref = get_page_ref("content", page, self._make_config())
        assert md == "content"
        assert ref is None

    def test_no_ref_section(self) -> None:
        page = self._make_page()
        _md, ref = get_page_ref("# Title\nBody text", page, self._make_config())
        assert ref is None

    def test_extracts_ref_section(self) -> None:
        page = self._make_page()
        content = "---\nid: 1\n---\n# Title\nBody\n---\nRef line 1\nRef line 2\n---"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "Ref line 1" in page.meta["ref"]
        assert "Ref line 2" in page.meta["ref"]
