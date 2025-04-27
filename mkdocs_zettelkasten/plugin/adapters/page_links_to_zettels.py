from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

if TYPE_CHECKING:
    from re import Match

import logging

from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def adapt_page_links_to_zettels(
    markdown: str,
    page: Page,
    config: MkDocsConfig,
    files: Files,
    zettel_service: ZettelService,
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
                if f.page and (
                    title == url_with_suffix or title + ".md" == url_with_suffix
                ):
                    target_zettel = zettel_service.get_zettel_by_partial_path(
                        url_with_suffix
                    )
                    title = target_zettel.title if target_zettel else url
                new_url = config["site_url"] + f.url
                logger.debug(
                    "Transformed link %s to [%s](%s) in %s",
                    m.group(),
                    title,
                    new_url,
                    page.file.src_path,
                )

                return f"[{title}]({new_url})"

        if f"[{title}]({url})" != m.group():
            logger.debug(
                "Transformed link %s to [%s](%s) in %s",
                m.group(),
                title,
                url,
                page.file.src_path,
            )

        return f"[{title}]({url})"

    markdown = WIKI_LINK.sub(process_match, markdown)

    return MD_LINK.sub(process_match, markdown)
