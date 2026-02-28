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


def adapt_mentions_to_page(
    page: Page,
    mentions: dict[int, list[tuple[int, str]]],
    zettel_lookup: Callable[[int], Zettel | None],
) -> None:
    """Add unlinked mentions to target zettels when the source page matches."""
    if not page.meta.get("is_zettel"):
        return

    zettel_meta = page.meta.get("zettel")
    if not zettel_meta:
        return

    source_id = zettel_meta.id

    for target_id, source_list in mentions.items():
        for src_id, snippet in source_list:
            if src_id != source_id:
                continue

            target_zettel = zettel_lookup(target_id)
            if not target_zettel:
                continue

            target_zettel.unlinked_mentions.append({
                "url": str(page.url),
                "title": str(page.title or ""),
                "snippet": snippet,
            })

            logger.debug(
                "Added unlinked mention from %s to zettel %s",
                page.url,
                target_id,
            )
