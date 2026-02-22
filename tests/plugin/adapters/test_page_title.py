from unittest.mock import MagicMock

import pytest
from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title


@pytest.fixture
def page() -> Page:
    page = MagicMock()
    page.file.abs_src_path = "/test/path.md"
    return page


def test_no_zettel(page: Page) -> None:
    """Should return original markdown if no zettel."""
    markdown = "Some content"
    result = adapt_page_title(markdown, page, None)
    assert result == markdown


def test_preserve_existing_h1(page: Page) -> None:
    """Should not modify markdown if H1 already exists."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"

    markdown = "# Existing Title\nSome content"
    result = adapt_page_title(markdown, page, zettel)
    assert result == markdown


def test_add_h1_when_missing(page: Page) -> None:
    """Should prepend zettel title if no H1 exists."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"

    markdown = "Some content"
    expected = "# Zettel Title\nSome content"
    result = adapt_page_title(markdown, page, zettel)
    assert result == expected


def test_ignore_leading_whitespace_in_h1(page: Page) -> None:
    """Should detect H1 even with leading whitespace."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"

    markdown = "   # Existing Title\nSome content"
    result = adapt_page_title(markdown, page, zettel)
    assert result == markdown


def test_blank_lines_before_content(page: Page) -> None:
    """Should add H1 if first non-blank line is not H1."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"

    markdown = "\n\nSome content"
    expected = "# Zettel Title\n\n\nSome content"
    result = adapt_page_title(markdown, page, zettel)
    assert result == expected
