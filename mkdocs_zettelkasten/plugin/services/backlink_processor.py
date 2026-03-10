import logging
from collections import defaultdict

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

from .zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class BacklinkProcessor:
    """Manages backlink relationships between zettels."""

    @classmethod
    def process(
        cls,
        store: ZettelStore,
        resolved_links: dict[int, set[int]],
    ) -> dict[int, list[Zettel]]:
        """Create mapping: target_zettel_id -> list_of_linking_zettels."""
        backlinks: dict[int, list[Zettel]] = defaultdict(list)

        for zettel in store.zettels:
            for target_id in resolved_links.get(zettel.id, set()):
                logger.debug(
                    "Link from %s to %s found and added to %s's backlinks.",
                    zettel.id,
                    target_id,
                    target_id,
                )
                backlinks[target_id].append(zettel)

        return backlinks
