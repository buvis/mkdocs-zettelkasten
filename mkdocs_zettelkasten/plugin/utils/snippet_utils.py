"""Shared snippet truncation logic for backlinks and mentions."""

_MAX_LEN = 200


def truncate_around(text: str, position: int, marker_len: int) -> str:
    """Truncate text to ~200 chars centered on position, expanding to word boundaries."""
    if len(text) <= _MAX_LEN:
        return text

    half = _MAX_LEN // 2
    start = max(0, position - half)
    end = min(len(text), position + marker_len + half)

    if start > 0:
        space = text.rfind(" ", 0, start)
        start = space + 1 if space != -1 else start
    if end < len(text):
        space = text.find(" ", end)
        end = space if space != -1 else end

    snippet = text[start:end]
    if start > 0:
        snippet = "..." + snippet
    if end < len(text):
        snippet = snippet + "..."
    return snippet
