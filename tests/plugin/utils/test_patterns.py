from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK


class TestWikiLink:
    def test_simple_wiki_link(self) -> None:
        match = WIKI_LINK.search("[[target]]")
        assert match is not None
        assert match.group("url") == "target"
        assert match.group("title") is None

    def test_wiki_link_with_alias(self) -> None:
        match = WIKI_LINK.search("[[target|alias text]]")
        assert match is not None
        assert match.group("url") == "target"
        assert match.group("title") == "alias text"

    def test_multiple_wiki_links(self) -> None:
        matches = list(WIKI_LINK.finditer("see [[one]] and [[two|second]]"))
        assert len(matches) == 2
        assert matches[0].group("url") == "one"
        assert matches[1].group("url") == "two"
        assert matches[1].group("title") == "second"

    def test_wiki_link_with_numeric_id(self) -> None:
        match = WIKI_LINK.search("[[20240101120000]]")
        assert match is not None
        assert match.group("url") == "20240101120000"

    def test_no_wiki_link(self) -> None:
        assert WIKI_LINK.search("no links here") is None

    def test_empty_wiki_link(self) -> None:
        assert WIKI_LINK.search("[[]]") is None


class TestMdLink:
    def test_simple_md_link(self) -> None:
        match = MD_LINK.search("[text](url)")
        assert match is not None
        assert match.group("title") == "text"
        assert match.group("url") == "url"

    def test_md_link_with_path(self) -> None:
        match = MD_LINK.search("[my page](path/to/page.md)")
        assert match is not None
        assert match.group("title") == "my page"
        assert match.group("url") == "path/to/page.md"

    def test_multiple_md_links(self) -> None:
        matches = list(MD_LINK.finditer("[a](1) and [b](2)"))
        assert len(matches) == 2
        assert matches[0].group("url") == "1"
        assert matches[1].group("url") == "2"

    def test_no_md_link(self) -> None:
        assert MD_LINK.search("no links here") is None

    def test_md_link_empty_text(self) -> None:
        match = MD_LINK.search("[](url)")
        assert match is not None
        assert match.group("title") == ""
        assert match.group("url") == "url"
