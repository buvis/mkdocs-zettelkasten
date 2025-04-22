import re

WIKI_LINK = re.compile(r"\[\[(?P<url>.*?)\]\]", re.MULTILINE)
MD_LINK = re.compile(r"\[(?P<title>.*?)\]\((?P<url>.*?)\)", re.MULTILINE)
