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


def adapt_suggestions_to_page(
    page: Page,
    suggestions: dict[int, list[dict]],
    zettel_lookup: Callable[[int], Zettel | None],
    file_suffix: str = ".md",
) -> None:
    """Attach link suggestions to the current page's zettel."""
    if not page.meta.get("is_zettel"):
        return

    zettel = page.meta.get("zettel")
    if not zettel:
        return

    source_id = zettel.id
    sugg_list = suggestions.get(source_id, [])

    for sugg in sugg_list:
        target = zettel_lookup(sugg["target_id"])
        if not target:
            continue

        url = target.rel_path.removesuffix(file_suffix) + "/"
        zettel.suggested_links.append({
            "url": url,
            "title": target.title,
            "reason": sugg["reason"],
            "confidence": f"{int(sugg['confidence'] * 100)}%",
        })

    logger.debug(
        "Attached %d suggestions to zettel %s",
        len(zettel.suggested_links),
        source_id,
    )
