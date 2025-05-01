import logging

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.adapters.backlinks_to_page import (
    adapt_backlinks_to_page,
)
from mkdocs_zettelkasten.plugin.adapters.page_links_to_zettels import (
    adapt_page_links_to_zettels,
)
from mkdocs_zettelkasten.plugin.adapters.page_ref import get_page_ref
from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title
from mkdocs_zettelkasten.plugin.adapters.prev_next_page import get_prev_next_page
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class PageTransformer:
    """
    Applies all Zettelkasten-specific transformations to page markdown.
    """

    def transform(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
        zettel_service: ZettelService,
    ) -> str:
        """
        Apply all adapters to the markdown and update references.
        """
        logger.debug("Started %s transformations", page.file.src_path)
        page = zettel_service.add_zettel_to_page(page)
        markdown = adapt_page_title(markdown, page, zettel_service)
        markdown = adapt_page_links_to_zettels(
            markdown, page, config, files, zettel_service
        )
        processed_md, page.meta["ref"] = get_page_ref(markdown, page, config)
        page.previous_page, page.next_page = get_prev_next_page(
            page, files, zettel_service.get_zettels()
        )
        adapt_backlinks_to_page(page, zettel_service)
        logger.debug("Finished %s transformations", page.file.src_path)

        return processed_md
