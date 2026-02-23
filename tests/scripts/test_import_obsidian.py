from import_obsidian import (
    convert_file_content,
    convert_links,
    map_frontmatter,
    slugify_filename,
)


class TestSlugifyFilename:
    def test_spaces_to_hyphens(self) -> None:
        assert slugify_filename("My Cool Note") == "my-cool-note"

    def test_multiple_spaces(self) -> None:
        assert slugify_filename("a   b") == "a-b"

    def test_already_slug(self) -> None:
        assert slugify_filename("already-slug") == "already-slug"

    def test_mixed_case(self) -> None:
        assert slugify_filename("CamelCase") == "camelcase"

    def test_strips_whitespace(self) -> None:
        assert slugify_filename("  padded  ") == "padded"


class TestConvertWikiLinks:
    def test_simple(self) -> None:
        assert convert_links("[[target]]") == "[target](target.md)"

    def test_with_alias(self) -> None:
        assert convert_links("[[target|display]]") == "[display](target.md)"

    def test_spaces_in_target(self) -> None:
        assert convert_links("[[My Note]]") == "[My Note](my-note.md)"

    def test_spaces_with_alias(self) -> None:
        assert convert_links("[[My Note|click here]]") == "[click here](my-note.md)"

    def test_multiple_links(self) -> None:
        text = "see [[one]] and [[two|second]]"
        result = convert_links(text)
        assert result == "see [one](one.md) and [second](two.md)"

    def test_inline_with_text(self) -> None:
        text = "Check out [[note]] for details."
        assert convert_links(text) == "Check out [note](note.md) for details."


class TestConvertEmbedLinks:
    def test_simple_embed(self) -> None:
        assert convert_links("![[target]]") == "![target](target.md)"

    def test_embed_with_section(self) -> None:
        assert convert_links("![[target#heading]]") == "![target](target.md#heading)"

    def test_embed_with_section_spaces(self) -> None:
        result = convert_links("![[target#My Heading]]")
        assert result == "![target](target.md#my-heading)"

    def test_embed_with_alias(self) -> None:
        assert convert_links("![[target|alt]]") == "![alt](target.md)"

    def test_embed_with_section_and_alias(self) -> None:
        result = convert_links("![[target#sec|alt]]")
        assert result == "![alt](target.md#sec)"

    def test_embed_spaces_in_target(self) -> None:
        assert convert_links("![[My Note]]") == "![My Note](my-note.md)"

    def test_embed_not_confused_with_regular(self) -> None:
        text = "![[embed]] and [[link]]"
        result = convert_links(text)
        assert result == "![embed](embed.md) and [link](link.md)"


class TestMapFrontmatter:
    def test_strips_obsidian_keys(self) -> None:
        fm = {"title": "Test", "aliases": ["a"], "cssclass": "wide"}
        result = map_frontmatter(fm)
        assert result == {"title": "Test"}

    def test_preserves_unknown_keys(self) -> None:
        fm = {"title": "Test", "tags": ["a", "b"]}
        result = map_frontmatter(fm)
        assert result == {"title": "Test", "tags": ["a", "b"]}

    def test_custom_mapping_rename(self) -> None:
        fm = {"old_key": "val", "keep": True}
        result = map_frontmatter(fm, {"old_key": "new_key"})
        assert result == {"new_key": "val", "keep": True}

    def test_custom_mapping_strip(self) -> None:
        fm = {"drop_me": "val", "keep": True}
        result = map_frontmatter(fm, {"drop_me": None})
        assert result == {"keep": True}

    def test_empty_frontmatter(self) -> None:
        assert map_frontmatter({}) == {}


class TestConvertFileContent:
    def test_body_only(self) -> None:
        text = "Some text with [[link]]."
        assert convert_file_content(text) == "Some text with [link](link.md)."

    def test_with_frontmatter(self) -> None:
        text = "---\ntitle: Hello\n---\nBody with [[link]]."
        result = convert_file_content(text)
        assert "title: Hello" in result
        assert "[link](link.md)" in result
        assert result.startswith("---\n")

    def test_frontmatter_strips_obsidian_keys(self) -> None:
        text = "---\ntitle: Hello\naliases:\n  - hi\ncssclass: wide\n---\nBody."
        result = convert_file_content(text)
        assert "aliases" not in result
        assert "cssclass" not in result
        assert "title: Hello" in result

    def test_frontmatter_with_embeds(self) -> None:
        text = "---\ntitle: T\n---\n![[embed#sec]]"
        result = convert_file_content(text)
        assert "![embed](embed.md#sec)" in result

    def test_no_frontmatter_with_hrule(self) -> None:
        text = "Some text\n\n---\n\nMore text"
        result = convert_file_content(text)
        assert result == text
