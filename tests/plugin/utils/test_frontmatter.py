from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter


class TestParseFrontmatter:
    def test_splits_header_and_body(self) -> None:
        header, body, has_opening = parse_frontmatter("---\nid: 1\ntitle: Test\n---\nbody text\n")
        assert "id: 1" in header
        assert "title: Test" in header
        assert "body text" in body
        assert has_opening is True

    def test_no_frontmatter_returns_empty_header(self) -> None:
        header, body, has_opening = parse_frontmatter("just text\n")
        assert header == ""
        assert "just text" in body
        assert has_opening is False

    def test_unclosed_frontmatter_returns_empty_header(self) -> None:
        header, _body, has_opening = parse_frontmatter("---\nid: 1\n")
        assert header == ""
        assert has_opening is True

    def test_empty_string(self) -> None:
        header, body, has_opening = parse_frontmatter("")
        assert header == ""
        assert body == ""
        assert has_opening is False

    def test_empty_frontmatter(self) -> None:
        header, body, has_opening = parse_frontmatter("---\n---\nbody\n")
        assert header == ""
        assert "body" in body
        assert has_opening is True

    def test_whitespace_only_body(self) -> None:
        header, body, has_opening = parse_frontmatter("---\nid: 1\n---\n   \n")
        assert "id: 1" in header
        assert body.strip() == ""
        assert has_opening is True

    def test_no_body_after_frontmatter(self) -> None:
        header, body, has_opening = parse_frontmatter("---\nid: 1\n---\n")
        assert "id: 1" in header
        assert body == ""
        assert has_opening is True

    def test_no_trailing_newline(self) -> None:
        header, body, has_opening = parse_frontmatter("---\nid: 1\n---\nbody")
        assert "id: 1" in header
        assert body == "body"
        assert has_opening is True

    def test_bom_before_first_divider(self) -> None:
        # BOM (\ufeff) before the opening --- makes the divider line "\ufeff---"
        # which doesn't match "---", so the first divider is skipped.
        # The closing --- is seen as a lone opening divider → unclosed pattern.
        header, _body, has_opening = parse_frontmatter("\ufeff---\nid: 1\n---\nbody\n")
        assert header == ""
        assert has_opening is True

    def test_bom_stripped_before_parse(self) -> None:
        # After stripping BOM, frontmatter should parse normally.
        content = "\ufeff---\nid: 1\n---\nbody\n"
        header, body, has_opening = parse_frontmatter(content.lstrip("\ufeff"))
        assert "id: 1" in header
        assert "body" in body
        assert has_opening is True

    def test_extra_divider_in_body(self) -> None:
        header, body, has_opening = parse_frontmatter("---\nid: 1\n---\nbefore\n---\nafter\n")
        assert "id: 1" in header
        assert "before" in body
        assert "---" in body
        assert "after" in body
        assert has_opening is True

    def test_malformed_yaml_still_splits(self) -> None:
        # parse_frontmatter only splits text, it doesn't validate YAML
        header, body, has_opening = parse_frontmatter('---\nkey: "unclosed\n---\nbody\n')
        assert '"unclosed' in header
        assert "body" in body
        assert has_opening is True

    def test_divider_with_trailing_spaces(self) -> None:
        header, body, has_opening = parse_frontmatter("---  \nid: 1\n---  \nbody\n")
        assert "id: 1" in header
        assert "body" in body
        assert has_opening is True

    def test_only_dividers(self) -> None:
        header, body, has_opening = parse_frontmatter("---\n---\n")
        assert header == ""
        assert body == ""
        assert has_opening is True

    def test_crlf_line_endings(self) -> None:
        header, body, has_opening = parse_frontmatter("---\r\nid: 1\r\n---\r\nbody\r\n")
        assert "id: 1" in header
        assert "body" in body
        assert has_opening is True

    def test_multiline_yaml_value(self) -> None:
        content = "---\ntags:\n  - one\n  - two\n---\nbody\n"
        header, body, has_opening = parse_frontmatter(content)
        assert "tags:" in header
        assert "- one" in header
        assert "- two" in header
        assert "body" in body
        assert has_opening is True

    def test_whitespace_only_file(self) -> None:
        header, body, has_opening = parse_frontmatter("   \n\n  \n")
        assert header == ""
        assert has_opening is False

    def test_text_then_divider_is_absent(self) -> None:
        # Opening --- must be first divider; text before it means no frontmatter intent
        # but the function sees a --- so has_opening is True (unclosed pattern)
        header, _body, has_opening = parse_frontmatter("some text\n---\nmore text\n")
        assert header == ""
        assert has_opening is True
