from unittest.mock import MagicMock

import pytest
from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService


@pytest.fixture
def page() -> Page:
    page = MagicMock()
    page.file.abs_src_path = "/test/path.md"
    return page


@pytest.fixture
def zettel_service() -> MagicMock:
    return MagicMock()


def test_no_abs_src_path(page: Page, zettel_service: ZettelService) -> None:
    """Should return original markdown if abs_src_path is missing."""
    page.file.abs_src_path = None
    markdown = "Some content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == markdown


def test_no_zettel_found(page: Page, zettel_service: ZettelService) -> None:
    """Should return original markdown if no zettel is found."""
    zettel_service.get_zettel_by_path.return_value = None  # type: ignore[attr-defined]
    markdown = "Some content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == markdown


def test_preserve_existing_h1(page: Page, zettel_service: ZettelService) -> None:
    """Should not modify markdown if H1 already exists."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"
    zettel_service.get_zettel_by_path.return_value = zettel  # type: ignore[attr-defined]

    markdown = "# Existing Title\nSome content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == markdown


def test_add_h1_when_missing(page: Page, zettel_service: ZettelService) -> None:
    """Should prepend zettel title if no H1 exists."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"
    zettel_service.get_zettel_by_path.return_value = zettel  # type: ignore[attr-defined]

    markdown = "Some content"
    expected = "# Zettel Title\nSome content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == expected


def test_ignore_leading_whitespace_in_h1(
    page: Page,
    zettel_service: ZettelService,
) -> None:
    """Should detect H1 even with leading whitespace."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"
    zettel_service.get_zettel_by_path.return_value = zettel  # type: ignore[attr-defined]

    markdown = "   # Existing Title\nSome content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == markdown


def test_blank_lines_before_content(page: Page, zettel_service: ZettelService) -> None:
    """Should add H1 if first non-blank line is not H1."""
    zettel = MagicMock()
    zettel.title = "Zettel Title"
    zettel_service.get_zettel_by_path.return_value = zettel  # type: ignore[attr-defined]

    markdown = "\n\nSome content"
    expected = "# Zettel Title\n\n\nSome content"
    result = adapt_page_title(markdown, page, zettel_service)
    assert result == expected
