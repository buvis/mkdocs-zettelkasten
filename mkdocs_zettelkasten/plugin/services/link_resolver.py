from __future__ import annotations

import logging
from collections import defaultdict
from typing import TYPE_CHECKING, NamedTuple

if TYPE_CHECKING:
    from .zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)

_EXTERNAL_PREFIXES = ("http://", "https://", "#", "mailto:")


class LinkMap(NamedTuple):
    resolved: dict[int, set[int]]
    broken: list[tuple[str, str]]


class LinkResolver:
    """Builds a pre-resolved link map from the zettel store."""

    @classmethod
    def resolve(cls, store: ZettelStore, file_suffix: str = ".md") -> LinkMap:
        """Resolve every zettel's links in a single pass.

        Returns a LinkMap with:
        - resolved: source zettel ID -> set of target zettel IDs
        - broken: list of (source rel_path, raw link) for unresolved internal links
        """
        resolved: dict[int, set[int]] = defaultdict(set)
        broken: list[tuple[str, str]] = []

        for zettel in store.zettels:
            for link in zettel.links:
                if link.startswith(_EXTERNAL_PREFIXES):
                    continue
                target = store.get_by_partial_path(link, file_suffix)
                if target is not None:
                    resolved[zettel.id].add(target.id)
                else:
                    broken.append((zettel.rel_path, link))

        # Ensure every zettel has an entry even if it has no resolved links
        for zettel in store.zettels:
            resolved.setdefault(zettel.id, set())

        logger.debug(
            "Link resolution: %d sources, %d broken links",
            len(resolved),
            len(broken),
        )
        return LinkMap(resolved=dict(resolved), broken=broken)
