import logging
from pathlib import Path

from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def adapt_page_title(markdown: str, page: Page, zettel_service: ZettelService) -> str:
    """
    Ensures the markdown has an H1 title. If missing, prepends the zettel's title.

    :param markdown: The markdown content of the page.
    :param page: The MkDocs Page object.
    :param zettel_service: Service to fetch zettel metadata.
    :return: Markdown with an H1 title at the top.
    """
    if not page.file.abs_src_path:
        return markdown

    zettel = zettel_service.get_zettel_by_path(Path(page.file.abs_src_path))

    if not zettel:
        return markdown

    if has_h1_title(markdown):
        return markdown

    logger.debug("Adding H1 with title to %s", page.url)

    return prepend_h1_title(markdown, zettel.title)


def has_h1_title(markdown: str) -> bool:
    """
    Checks if the markdown contains a non-empty H1 title as the first non-blank line.
    """
    for line in markdown.splitlines():
        if line.strip():  # skip blank lines
            return line.lstrip().startswith("# ")
    return False


def prepend_h1_title(markdown: str, title: str) -> str:
    """
    Prepends an H1 title to the markdown.
    """
    return f"# {title}\n{markdown}"
