from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import logging

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
