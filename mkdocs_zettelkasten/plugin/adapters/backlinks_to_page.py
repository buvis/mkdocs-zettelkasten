from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable

    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import LinkRef, Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def _find_snippet(source: Zettel, target: Zettel, file_suffix: str) -> str | None:
    """Find the snippet for a link from source to target.

    Tries matching by target ID (wiki links) and rel_path (md links).
    """
    candidates = [
        str(target.id),
        target.rel_path,
        target.rel_path.removesuffix(file_suffix),
    ]
    for key in candidates:
        if snippet := source.link_snippets.get(key):
            return snippet
    return None


def add_backlink_to_target(
    target_id: int,
    page: Page,
    zettel: Zettel,
    zettel_by_id: Callable[[int], Zettel | None],
    file_suffix: str = ".md",
) -> None:
    """Add a backlink to the target zettel if the source zettel matches the page."""
    zettel_meta = page.meta.get("zettel")
    if not zettel_meta or zettel.id != zettel_meta.id:
        return

    target_zettel = zettel_by_id(target_id)

    if not target_zettel:
        return

    snippet = _find_snippet(zettel, target_zettel, file_suffix)
    backlink: LinkRef = {
        "url": str(page.url or ""),
        "title": str(page.title or ""),
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
    backlinks: dict[int, list[Zettel]],
    zettel_by_id: Callable[[int], Zettel | None],
    file_suffix: str = ".md",
) -> None:
    """Adapts backlinks to the specified page by adding them to target Zettels."""
    if not page.meta.get("is_zettel"):
        return

    for target_id, source_zettels in backlinks.items():
        for zettel in source_zettels:
            add_backlink_to_target(target_id, page, zettel, zettel_by_id, file_suffix)
