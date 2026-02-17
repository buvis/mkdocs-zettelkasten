import logging
from collections import defaultdict
from collections.abc import Iterable

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

from .zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class BacklinkProcessor:
    """Manages backlink relationships between zettels."""

    @classmethod
    def process(
        cls, store: ZettelStore, file_suffix: str = ".md"
    ) -> dict[str, list[Zettel]]:
        """Create mapping: target_path -> list_of_linking_files."""
        backlinks = defaultdict(list)

        for zettel in store.zettels:
            for normalized_link in cls._normalize_links(zettel.links, file_suffix):
                target_zettel = store.get_by_partial_path(
                    normalized_link, file_suffix
                )

                if target_zettel:
                    logger.debug(
                        "Link from %s to %s found and added to %s's backlinks.",
                        zettel.id,
                        target_zettel.id,
                        target_zettel.id,
                    )
                    backlinks[normalized_link].append(zettel)

        return backlinks

    @staticmethod
    def _normalize_links(
        links: Iterable[str], file_suffix: str = ".md"
    ) -> set[str]:
        """Normalize links to consistent format with file suffix."""
        return {
            f"{link}{file_suffix}" if not link.endswith(file_suffix) else link
            for link in links
        }
