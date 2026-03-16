from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable
    from re import Match

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

import logging
import re

from mkdocs_zettelkasten.plugin.utils.frontmatter import DIVIDER
from mkdocs_zettelkasten.plugin.utils.patterns import (
    EMBED_LINK,
    process_outside_code_blocks,
)

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def _body_without_refs(body: str) -> str:
    """Return body content before the reference section divider."""
    for i, line in enumerate(body.splitlines(keepends=True)):
        if line.strip() == DIVIDER:
            return "".join(body.splitlines(keepends=True)[:i])
    return body


_HEADING_RE = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def _extract_section(body: str, section_name: str) -> str | None:
    """Extract a heading section from markdown body. Case-insensitive exact match."""
    target = section_name.strip().lower()
    start_pos = None
    start_level = 0

    for m in _HEADING_RE.finditer(body):
        level = len(m.group(1))
        title = m.group(2).strip().lower()

        if start_pos is None:
            if title == target:
                start_pos = m.start()
                start_level = level
        elif level <= start_level:
            return body[start_pos : m.start()]

    if start_pos is not None:
        return body[start_pos:]
    return None


_H1_RE = re.compile(r"^#\s+.+\n?", re.MULTILINE)


def adapt_transclusion(
    markdown: str,
    zettel_lookup: Callable[[str], Zettel | None],
    site_url: str,
    file_suffix: str = ".md",
    *,
    strip_heading: bool = True,
    max_embed_depth: int = 5,
    _depth: int = 0,
    _embed_stack: frozenset[str] | None = None,
) -> str:
    """Replace ![[id]] embed syntax with transcluded zettel content."""
    if _embed_stack is None:
        _embed_stack = frozenset()

    def _process(text: str) -> str:
        return EMBED_LINK.sub(
            lambda m: _resolve_embed(
                m,
                zettel_lookup,
                site_url,
                file_suffix,
                strip_heading,
                max_embed_depth,
                _depth,
                _embed_stack,
            ),
            text,
        )

    return process_outside_code_blocks(markdown, _process)


def _resolve_embed(
    m: Match,
    zettel_lookup: Callable[[str], Zettel | None],
    site_url: str,
    file_suffix: str,
    strip_heading: bool,  # noqa: FBT001
    max_embed_depth: int,
    depth: int,
    embed_stack: frozenset[str],
) -> str:
    url = m.group("url")
    section = m.group("section")
    title_override = m.group("title")

    url_with_suffix = url + file_suffix if not url.endswith(file_suffix) else url
    zettel = zettel_lookup(url_with_suffix)

    if zettel is None:
        logger.warning("Embed target not found: %s", url)
        return f'\n!!! warning "Embed not found"\n    Could not resolve embed target: `{url}`\n'

    zettel_key = str(zettel.path)
    if zettel_key in embed_stack:
        logger.warning("Circular embed detected: %s", url)
        return f'\n!!! warning "Circular embed"\n    Circular reference detected: `{url}`\n'

    body = _body_without_refs(zettel.body)

    if section:
        extracted = _extract_section(body, section)
        if extracted is None:
            logger.warning("Section '%s' not found in %s", section, url)
            return f'\n!!! warning "Section not found"\n    Could not find section "{section}" in `{url}`\n'
        body = extracted
        if strip_heading:
            body = _HEADING_RE.sub("", body, count=1)
    elif strip_heading:
        body = _H1_RE.sub("", body, count=1)

    if depth < max_embed_depth:
        body = adapt_transclusion(
            body,
            zettel_lookup,
            site_url,
            file_suffix,
            strip_heading=strip_heading,
            max_embed_depth=max_embed_depth,
            _depth=depth + 1,
            _embed_stack=embed_stack | {zettel_key},
        )

    display_title = title_override or zettel.title
    link_url = site_url.rstrip("/") + "/" + url + "/"
    header = f'<div class="zettel-embed-header"><a href="{link_url}">{display_title}</a></div>'

    return (
        f'\n<div class="zettel-embed">\n{header}\n'
        f'<div class="zettel-embed-content">\n\n{body.strip()}\n\n</div>\n</div>\n'
    )
