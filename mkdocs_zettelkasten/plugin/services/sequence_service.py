from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore

import logging

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class SequenceService:
    """Builds Folgezettel tree from sequence metadata."""

    @staticmethod
    def build_tree(store: ZettelStore) -> dict[int, list[int]]:
        """Build parent_id -> [child_ids] mapping, children sorted by ID."""
        children: dict[int, list[int]] = defaultdict(list)
        for z in store.zettels:
            if z.sequence_parent_id is not None:
                children[z.sequence_parent_id].append(z.id)
        for k in children:
            children[k].sort()

        total = sum(len(v) for v in children.values())
        logger.info("Built sequence tree: %d parent-child relations", total)
        return dict(children)
