import re

WIKI_LINK = re.compile(
    r"\[\[(?P<url>[^\]|]+)(?:\|(?P<title>[^\]]+))?\]\]", re.MULTILINE
)
MD_LINK = re.compile(r"\[(?P<title>.*?)\]\((?P<url>.*?)\)", re.MULTILINE)
EMBED_LINK = re.compile(
    r"!\[\[(?P<url>[^\]#|]+)(?:#(?P<section>[^\]|]+))?(?:\|(?P<title>[^\]]+))?\]\]",
    re.MULTILINE,
)
