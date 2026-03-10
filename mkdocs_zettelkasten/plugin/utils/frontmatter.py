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

    Only a ``---`` on the first line counts as a frontmatter opener.
    Later ``---`` lines without a first-line opener are thematic breaks.
    """
    lines = content.splitlines(keepends=True)
    if not lines or lines[0].strip() != DIVIDER:
        return ("", content, False)

    for i, line in enumerate(lines[1:], start=1):
        if line.strip() == DIVIDER:
            header = "".join(lines[1:i])
            body = "".join(lines[i + 1 :])
            return (header, body, True)

    return ("", content, True)
