import re
from collections.abc import Callable

WIKI_LINK = re.compile(
    r"\[\[(?P<url>[^\]|]+)(?:\|(?P<title>[^\]]+))?\]\]", re.MULTILINE
)
MD_LINK = re.compile(r"(?<!!)\[(?P<title>.*?)\]\((?P<url>.*?)\)", re.MULTILINE)
EMBED_LINK = re.compile(
    r"!\[\[(?P<url>[^\]#|]+)(?:#(?P<section>[^\]|]+))?(?:\|(?P<title>[^\]]+))?\]\]",
    re.MULTILINE,
)

_CODE_FENCE = re.compile(r"```", re.DOTALL)


def process_outside_code_blocks(markdown: str, processor: Callable[[str], str]) -> str:
    """Apply *processor* only to text outside fenced code blocks."""
    parts = _CODE_FENCE.split(markdown)
    for i in range(0, len(parts), 2):
        parts[i] = processor(parts[i])
    return "```".join(parts)
