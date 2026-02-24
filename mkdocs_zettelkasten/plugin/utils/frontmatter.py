"""Shared frontmatter parsing — single source of truth for YAML header splitting."""

from __future__ import annotations

DIVIDER = "---"
DIVIDER_COUNT = 2


def parse_frontmatter(content: str) -> tuple[str, str]:
    """Split content into (header_yaml_text, body_text) at YAML frontmatter boundary.

    Returns ("", content) if no valid frontmatter found.
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
                return (header, body)

    return ("", content)
