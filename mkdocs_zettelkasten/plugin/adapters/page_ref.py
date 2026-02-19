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

DIVIDER = Zettel.MARK_DIVIDER


def _find_divider_indices(content_lines: list[str]) -> list[int]:
    """Return indices of all ``---`` lines outside fenced code blocks."""
    indices: list[int] = []
    in_code_block = False

    for i, line in enumerate(content_lines):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
        elif not in_code_block and stripped == DIVIDER:
            indices.append(i)

    return indices


def get_page_ref(
    markdown: str,
    page: Page,
    config: MkDocsConfig,
) -> tuple[str, str | None]:
    """Extract reference section from page markdown (frontmatter already stripped)."""
    if not page.meta["is_zettel"]:
        return (markdown, None)

    content_lines = markdown.rstrip().split("\n")
    dividers = _find_divider_indices(content_lines)

    if not dividers:
        logger.debug("No reference section found in %s", page.file.src_path)
        return (markdown, None)

    last_line_is_divider = dividers[-1] == len(content_lines) - 1

    if last_line_is_divider and len(dividers) >= 2:
        # --- ... --- form: opening is second-to-last, closing is last
        open_idx = dividers[-2]
        end = dividers[-1]
    elif last_line_is_divider:
        # Single divider on last line — no ref content
        logger.debug("No reference section found in %s", page.file.src_path)
        return (markdown, None)
    else:
        # --- ... EOF form: last divider is opening, refs go to end
        open_idx = dividers[-1]
        end = len(content_lines)

    ref_lines = []
    for line in content_lines[open_idx + 1 : end]:
        if not line.strip():
            continue
        if line.lstrip().startswith("- "):
            ref_lines.append(line)
        else:
            ref_lines.append("- " + line)

    if not ref_lines:
        logger.debug("No reference section found in %s", page.file.src_path)
        return (markdown, None)

    markdown = "\n".join(content_lines[:open_idx])
    page.meta["ref"] = "\n".join(ref_lines)

    processor = Markdown(
        extensions=config["markdown_extensions"],
        extension_configs=config["mdx_configs"] or {},
    )

    logger.debug("Reference section found in %s", page.file.src_path)
    return (markdown, processor.convert(page.meta["ref"]))
