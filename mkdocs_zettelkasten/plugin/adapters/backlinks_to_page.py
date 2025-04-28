import logging

from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def adapt_backlinks_to_page(page: Page, zettel_service: ZettelService) -> None:
    """
    Update backlinks for zettels that link to the current page.

    :param page: The page whose backlinks should be updated.
    :param zettel_service: Service providing zettel and backlink information.
    """
    if not page.meta["is_zettel"]:
        return

    current_zettel_id = page.meta["zettel"].id

    for link, source_zettels in zettel_service.backlinks.items():
        for zettel in source_zettels:
            if zettel.id != current_zettel_id:
                continue

            target_zettel = zettel_service.get_zettel_by_partial_path(link)
            if not target_zettel:
                continue

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
