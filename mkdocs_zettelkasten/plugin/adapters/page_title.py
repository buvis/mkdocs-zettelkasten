from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def adapt_page_title(markdown: str, page: Page, zettel: Zettel | None) -> str:
    """Ensures the markdown has an H1 title. If missing, prepends the zettel's title."""
    if not zettel:
        return markdown

    if has_h1_title(markdown):
        return markdown

    logger.debug("Adding H1 with title to %s", page.url)

    return prepend_h1_title(markdown, zettel.title)


def has_h1_title(markdown: str) -> bool:
    """Checks if the markdown contains a non-empty H1 title as the first non-blank line."""
    for line in markdown.splitlines():
        if line.strip():
            return line.lstrip().startswith("# ")
    return False


def prepend_h1_title(markdown: str, title: str) -> str:
    """Prepends an H1 title to the markdown."""
    return f"# {title}\n{markdown}"
