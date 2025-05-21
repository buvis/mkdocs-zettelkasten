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
    Adds a backlink to the target zettel if the given zettel links to the page.

    This function checks if the zettel corresponds to the current page. If so,
    it finds the target zettel referenced by the link and appends a backlink
    entry to its backlinks list.

    Args:
        link (str): The link to the target zettel.
        page (Page): The current MkDocs page.
        zettel (Zettel): The zettel associated with the current page.
        zettel_service (ZettelService): Service to retrieve zettels.
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
    Update backlinks for zettels that link to the current page.

    :param page: The page whose backlinks should be updated.
    :type page: Page
    :param zettel_service: Service providing zettel and backlink information.
    :type zettel_service: ZettelService
    """

    if not page.meta["is_zettel"]:
        return

    for link, source_zettels in zettel_service.backlinks.items():
        for zettel in source_zettels:
            add_backlink_to_target(link, page, zettel, zettel_service)
