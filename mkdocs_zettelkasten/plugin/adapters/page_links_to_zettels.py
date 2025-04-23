from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from re import Match

from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK


def adapt_page_links_to_zettels(
    markdown: str,
    config: dict[str, Any],
    files: list[Any],
) -> str:
    """
    Adapt links in the markdown to point to zettels.
    """

    def process_match(m: Match) -> str:
        url = m.groupdict().get("url", "")
        title = m.groupdict().get("title", url)

        for f in files:
            url_with_suffix = url + ".md" if not url.endswith(".md") else url

            if url_with_suffix in f.src_path:
                if title == url_with_suffix or title + ".md" == url_with_suffix:
                    title = f.zettel.title
                new_url = config["site_url"] + f.url

                return f"[{title}]({new_url})"

        return f"[{title}]({url})"

    markdown = WIKI_LINK.sub(process_match, markdown)

    return MD_LINK.sub(process_match, markdown)
