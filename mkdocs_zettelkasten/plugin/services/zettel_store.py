from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

import logging

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class ZettelStore:
    """Storage for zettels with efficient lookup capabilities."""

    def __init__(self, zettels: Iterable[Zettel] = ()) -> None:
        self.update(zettels)

    @property
    def zettels(self) -> list[Zettel]:
        """View of stored zettels."""
        return list(self._zettels)

    def _rebuild_indexes(self) -> None:
        """Maintain internal indexes for fast lookups."""
        self._path_index = {z.path: z for z in self._zettels}

    def get_by_path(self, path: Path) -> Zettel | None:
        """Retrieve zettel by filesystem path."""
        return self._path_index.get(path)

    def get_by_partial_path(self, partial_path: str) -> Zettel | None:
        """Retrieve zettel by partial filesystem path."""
        partial_path.removesuffix(".md")

        for zettel in self.zettels:
            if partial_path in str(zettel.path):
                return zettel

        return None

    def update(self, zettels: Iterable[Zettel]) -> None:
        """Replace stored zettels with new collection."""
        sorted_zettels = sorted(zettels, key=lambda z: z.id)
        self._zettels = list(dict.fromkeys(sorted_zettels))
        self._rebuild_indexes()
        logger.info("Zettel store updated with %d zettels.", len(sorted_zettels))
