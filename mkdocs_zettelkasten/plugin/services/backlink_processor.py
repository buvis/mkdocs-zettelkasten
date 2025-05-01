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
    def process(cls, store: ZettelStore) -> dict[str, list[Zettel]]:
        """Create mapping: target_path -> list_of_linking_files."""
        backlinks = defaultdict(list)

        for zettel in store.zettels:
            for normalized_link in cls._normalize_links(zettel.links):
                target_zettel = store.get_by_partial_path(normalized_link)

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
    def _normalize_links(links: Iterable[str]) -> set[str]:
        """Normalize links to consistent Markdown format."""
        return {f"{link}.md" if not link.endswith(".md") else link for link in links}
