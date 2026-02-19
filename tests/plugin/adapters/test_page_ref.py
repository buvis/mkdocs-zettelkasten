from unittest.mock import MagicMock

from mkdocs_zettelkasten.plugin.adapters.page_ref import (
    _find_divider_indices,
    get_page_ref,
)


class TestFindDividerIndices:
    def test_no_dividers(self) -> None:
        assert _find_divider_indices(["line1", "line2"]) == []

    def test_returns_all_divider_indices(self) -> None:
        lines = ["---", "content", "---", "more"]
        assert _find_divider_indices(lines) == [0, 2]

    def test_ignores_dividers_in_code_blocks(self) -> None:
        lines = ["```", "---", "```", "---"]
        assert _find_divider_indices(lines) == [3]

    def test_all_dividers_in_code_blocks(self) -> None:
        lines = ["```", "---", "```", "text", "```", "---", "```"]
        assert _find_divider_indices(lines) == []


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
        content = "# Title\nBody\n---\nRef line 1\nRef line 2\n---"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "Ref line 1" in page.meta["ref"]
        assert "Ref line 2" in page.meta["ref"]

    def test_strips_ref_section_from_markdown(self) -> None:
        page = self._make_page()
        content = "# Title\nBody\n---\nsome ref\n---"
        md, _ref = get_page_ref(content, page, self._make_config())
        assert md == "# Title\nBody"

    def test_eof_form_without_closing_divider(self) -> None:
        page = self._make_page()
        content = "Body\n---\nref1\nref2"
        md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "ref1" in page.meta["ref"]
        assert "ref2" in page.meta["ref"]
        assert md == "Body"

    # Task 4: multi-format ref line tests

    def test_double_colon_format(self) -> None:
        page = self._make_page()
        content = "Body\n---\nsource:: some book"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: some book" in page.meta["ref"]

    def test_double_colon_wiki_link_with_title(self) -> None:
        page = self._make_page()
        content = "Body\n---\nsource:: [[path/to/note|My Note]]"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: [My Note](path/to/note)" in page.meta["ref"]

    def test_double_colon_wiki_link_without_title(self) -> None:
        page = self._make_page()
        content = "Body\n---\nsource:: [[path/to/note]]"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: [path/to/note](path/to/note)" in page.meta["ref"]

    def test_list_double_colon_format(self) -> None:
        page = self._make_page()
        content = "Body\n---\n- source:: [Example](https://example.com)"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: [Example](https://example.com)" in page.meta["ref"]

    def test_mixed_formats(self) -> None:
        page = self._make_page()
        content = (
            "Body\n---\n"
            "source:: some book\n"
            "- related:: [[note|Title]]\n"
            "web: [Site](https://example.com)"
        )
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: some book" in page.meta["ref"]
        assert "- related: [Title](note)" in page.meta["ref"]
        assert "- web: [Site](https://example.com)" in page.meta["ref"]

    def test_blank_lines_after_divider_skipped(self) -> None:
        page = self._make_page()
        content = "Body\n---\n\n\nsource:: value\n---"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- source: value" in page.meta["ref"]

    # Task 5: regression tests for existing web: style

    def test_existing_web_style_preserved(self) -> None:
        page = self._make_page()
        content = "Body\n---\nweb: [Example](https://example.com)\n---"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- web: [Example](https://example.com)" in page.meta["ref"]

    def test_multiple_existing_style_refs(self) -> None:
        page = self._make_page()
        content = (
            "Body\n---\n"
            "web: [One](https://one.com)\n"
            "web: [Two](https://two.com)\n---"
        )
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- web: [One](https://one.com)" in page.meta["ref"]
        assert "- web: [Two](https://two.com)" in page.meta["ref"]

    def test_old_and_new_formats_mixed(self) -> None:
        page = self._make_page()
        content = (
            "Body\n---\n"
            "web: [Site](https://example.com)\n"
            "source:: a book\n---"
        )
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "- web: [Site](https://example.com)" in page.meta["ref"]
        assert "- source: a book" in page.meta["ref"]

    # Task 6: code-fence safety tests

    def test_divider_in_code_fence_with_real_ref_section(self) -> None:
        page = self._make_page()
        content = "Body\n```yaml\nkey: value\n---\nmore: stuff\n```\n---\nactual: ref"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "actual: ref" in page.meta["ref"]
        assert "more: stuff" not in page.meta["ref"]

    def test_divider_in_code_fence_no_real_ref_section(self) -> None:
        page = self._make_page()
        content = "Body\n```yaml\nkey: value\n---\nmore: stuff\n```"
        _md, ref = get_page_ref(content, page, self._make_config())
        assert ref is None

    def test_code_fence_between_body_and_ref(self) -> None:
        page = self._make_page()
        content = (
            "Body\n```\ncode with ---\n```\n"
            "More body\n---\nref line\n---"
        )
        md, ref = get_page_ref(content, page, self._make_config())
        assert ref is not None
        assert "ref line" in page.meta["ref"]
        assert "```" in md
