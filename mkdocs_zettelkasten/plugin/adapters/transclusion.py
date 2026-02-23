from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import logging
import re

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def _read_zettel_body(path: Path) -> str:
    """Read a zettel file and return body content (after YAML header, before ref footer)."""
    lines = path.read_text(encoding="utf-8-sig").splitlines(keepends=True)
    body_lines: list[str] = []
    divider_count = 0

    for line in lines:
        if line.strip() == "---":
            divider_count += 1
            if divider_count >= 3:
                break
            continue
        if divider_count >= 2:
            body_lines.append(line)

    return "".join(body_lines)


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
