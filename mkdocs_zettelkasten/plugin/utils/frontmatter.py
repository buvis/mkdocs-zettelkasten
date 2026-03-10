"""Shared frontmatter parsing — single source of truth for YAML header splitting."""

from __future__ import annotations

DIVIDER = "---"
DIVIDER_COUNT = 2


def parse_frontmatter(content: str) -> tuple[str, str, bool]:
    """Split content into (header_yaml_text, body_text, has_opening) at YAML frontmatter boundary.

    Return cases:
        (header, body, True)   — valid frontmatter found and closed
        ("",   content, True)  — opening ``---`` found but never closed (malformed)
        ("",   content, False) — no opening ``---`` at all (not a zettel)
    """
    lines = content.splitlines(keepends=True)
    divider_count = 0
    header_start = 0

    for i, line in enumerate(lines):
        if line.strip() == DIVIDER:
            divider_count += 1
            if divider_count == 1:
                header_start = i + 1
            elif divider_count == DIVIDER_COUNT:
                header = "".join(lines[header_start:i])
                body = "".join(lines[i + 1 :])
                return (header, body, True)

    return ("", content, divider_count > 0)
