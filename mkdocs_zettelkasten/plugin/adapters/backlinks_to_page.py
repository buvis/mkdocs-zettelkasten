import logging

from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def add_backlink_to_target(
    link: str,
    page: Page,
    zettel: Zettel,
    zettel_service: ZettelService,
) -> None:
    """
    Add a backlink to the target zettel if the link and page match.

    Parameters:
    -----------

        - link (str): The link to be processed.
        - page (Page): The page containing the link.
        - zettel (Zettel): The current zettel being processed.
        - zettel_service (ZettelService): Service to get target zettel by partial path.
    """
    if zettel.id != page.meta["zettel"].id:
        return

    target_zettel = zettel_service.get_zettel_by_partial_path(link)

    if not target_zettel:
        return

    backlink = {
        "url": page.url,
        "title": page.title,
    }
    target_zettel.backlinks.append(backlink)
    logger.debug(
        "Found link from %s to %s. Adding it to %s's backlinks.",
        zettel.rel_path,
        target_zettel.rel_path,
        target_zettel.rel_path,
    )


def adapt_backlinks_to_page(page: Page, zettel_service: ZettelService) -> None:
    """
    Adapts backlinks to the specified page by adding them to the target Zettels.

    Parameters:
    -----------

        - page (Page): The Page object for which backlinks are being adapted.
        - zettel_service (ZettelService): The ZettelService used to fetch Zettels and manage
          backlinks.
    """
    if not page.meta["is_zettel"]:
        return

    for link, source_zettels in zettel_service.backlinks.items():
        for zettel in source_zettels:
            add_backlink_to_target(link, page, zettel, zettel_service)
