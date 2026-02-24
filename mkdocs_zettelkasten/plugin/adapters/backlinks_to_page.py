from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def add_backlink_to_target(
    link: str,
    page: Page,
    zettel: Zettel,
    zettel_lookup: Callable[[str], Zettel | None],
) -> None:
    """Add a backlink to the target zettel if the link and page match."""
    zettel_meta = page.meta.get("zettel")
    if not zettel_meta or zettel.id != zettel_meta.id:
        return

    target_zettel = zettel_lookup(link)

    if not target_zettel:
        return

    snippet = zettel.link_snippets.get(link) or zettel.link_snippets.get(
        link.removesuffix(".md")
    )
    backlink = {
        "url": page.url,
        "title": page.title,
        "snippet": snippet,
    }
    target_zettel.backlinks.append(backlink)

    if zettel.is_moc:
        target_zettel.moc_parents.append(backlink)

    logger.debug(
        "Found link from %s to %s. Adding it to %s's backlinks.",
        zettel.rel_path,
        target_zettel.rel_path,
        target_zettel.rel_path,
    )


def adapt_backlinks_to_page(
    page: Page,
    backlinks: dict[str, list[Zettel]],
    zettel_lookup: Callable[[str], Zettel | None],
) -> None:
    """Adapts backlinks to the specified page by adding them to target Zettels."""
    if not page.meta.get("is_zettel"):
        return

    for link, source_zettels in backlinks.items():
        for zettel in source_zettels:
            add_backlink_to_target(link, page, zettel, zettel_lookup)
