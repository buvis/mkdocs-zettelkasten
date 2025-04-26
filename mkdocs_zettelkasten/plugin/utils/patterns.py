import re

WIKI_LINK = re.compile(
    r"\[\[(?P<url>[^\]|]+)(?:\|(?P<title>[^\]]+))?\]\]", re.MULTILINE
)
MD_LINK = re.compile(r"\[(?P<title>.*?)\]\((?P<url>.*?)\)", re.MULTILINE)
