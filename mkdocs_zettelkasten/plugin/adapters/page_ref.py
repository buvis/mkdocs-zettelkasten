from __future__ import annotations

from typing import TYPE_CHECKING

from markdown import Markdown

if TYPE_CHECKING:
    import re

    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.pages import Page

import logging

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel
from mkdocs_zettelkasten.plugin.utils.patterns import WIKI_LINK

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


def _convert_wiki_link(text: str) -> str:
    """Replace ``[[path|title]]`` with ``[title](path)`` in *text*."""
    def _repl(m: re.Match) -> str:
        url = m.group("url")
        title = m.group("title") or url
        return f"[{title}]({url})"

    return WIKI_LINK.sub(_repl, text)


def _normalize_ref_line(line: str) -> str:
    """Normalize a single reference line to ``- key: value`` form."""
    stripped = line.strip()

    # Already a list item
    if stripped.startswith("- "):
        inner = stripped[2:]
        if "::" in inner:
            # "- key:: value" → "- key: value"
            inner = inner.replace("::", ":", 1)
        return "- " + _convert_wiki_link(inner)

    # Bare "key:: value"
    if "::" in stripped:
        normalized = stripped.replace("::", ":", 1)
        return "- " + _convert_wiki_link(normalized)

    # No :: — plain line, add list prefix
    return "- " + stripped


def get_page_ref(
    markdown: str,
    page: Page,
    config: MkDocsConfig,
) -> tuple[str, str | None]:
    """Extract reference section from page markdown (frontmatter already stripped)."""
    if not page.meta.get("is_zettel"):
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
        ref_lines.append(_normalize_ref_line(line))

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
