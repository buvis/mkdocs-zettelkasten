from __future__ import annotations

from typing import TYPE_CHECKING

from markdown import Markdown

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page

import logging

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def count_dividers_outside_code_blocks(
    content_lines: list[str],
    divider: str = Zettel.MARK_DIVIDER,
) -> int:
    """
    Count occurrences of a divider line outside code blocks in a list of lines.

    A code block starts with a line whose first three characters are '```
    (optionally followed by a language specifier) and ends with another such line.
    Divider lines inside code blocks are ignored.

    :param content_lines: List of lines to process.
    :param divider: The divider string to count (default: '---').
    :return: Number of divider lines outside code blocks.
    """
    count = 0
    in_code_block = False

    for line in content_lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
        elif not in_code_block and stripped == divider:
            count += 1

    return count


def get_page_ref(
    markdown: str,
    page: Page,
    config: MkDocsConfig,
) -> tuple[str, str | None]:
    """
    Add or extract a page reference.
    """
    if not page.meta["is_zettel"]:
        return (markdown, None)

    content_lines = markdown.rstrip().split("\n")

    # process footer from bottom till --- delimiter

    if content_lines[-1] == Zettel.MARK_DIVIDER:
        n = 2
    elif (
        count_dividers_outside_code_blocks(content_lines, Zettel.MARK_DIVIDER)
        > Zettel.COUNT_HEADER_DIVIDERS
    ):
        n = 1
    else:
        logger.debug("No reference section found in %s", page.file.src_path)
        return (markdown, None)

    ref_lines = []

    while content_lines[-n] != Zettel.MARK_DIVIDER and n < len(content_lines):
        ref_lines.append(" - " + content_lines[-n])
        n = n + 1

    # remove footer from page's markdown source
    markdown = "\n".join(content_lines[: -n - 1])
    # restore the order of references (as we went bottom->up)
    ref_lines.reverse()
    page.meta["ref"] = "\n".join(
        line for line in ref_lines if line.strip() and line.strip() != "-"
    )
    # convert the reference footer to HTML
    processor = Markdown(
        extensions=config["markdown_extensions"],
        extension_configs=config["mdx_configs"] or {},
    )

    logger.debug("Reference section found in %s", page.file.src_path)
    return (markdown, processor.convert(page.meta["ref"]))
