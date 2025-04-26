from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService


def adapt_backlinks_to_page(page: Page, zettel_service: ZettelService) -> None:
    if page.meta["is_zettel"]:
        for link, source_zettels in zettel_service.backlinks.items():
            for zettel in source_zettels:
                if zettel.id == page.meta["zettel"].id:
                    target_zettel = zettel_service.get_zettel_by_partial_path(link)
                    if target_zettel:
                        backlink = {}
                        backlink["url"] = page.url
                        backlink["title"] = page.title
                        target_zettel.backlinks.append(backlink)
