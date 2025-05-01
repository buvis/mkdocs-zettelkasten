from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from mkdocs.config.defaults import MkDocsConfig

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

import logging

from .backlink_processor import BacklinkProcessor
from .zettel_parser import ZettelParser
from .zettel_store import ZettelStore

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class ZettelService:
    """Orchestrates zettel processing pipeline."""

    def __init__(self) -> None:
        self.store = ZettelStore()
        self.backlinks: dict[str, list[Zettel]] = {}

    def process_files(self, files: Files, config: MkDocsConfig) -> None:
        """Main processing pipeline."""
        docs_dir = config["docs_dir"]
        logger.info("Scanning `%s` for zettels", docs_dir)
        valid_zettels, _ = ZettelParser.parse_files(files)
        logger.info("Found %s zettels in `%s`", len(valid_zettels), docs_dir)
        self.store.update(valid_zettels)
        self.backlinks = BacklinkProcessor.process(self.store)

    def add_zettel_to_page(self, page: Page) -> Page:
        enriched_page = page

        if not enriched_page.file.abs_src_path:
            enriched_page.meta["is_zettel"] = False
            return enriched_page

        zettel_for_page = self.get_zettel_by_path(Path(enriched_page.file.abs_src_path))

        if zettel_for_page:
            enriched_page.meta["zettel"] = zettel_for_page
            enriched_page.meta["is_zettel"] = True
            logger.debug("Added zettel to %s's metadata.", page.file.src_path)
        else:
            enriched_page.meta["is_zettel"] = False
            logger.debug(
                "Skipped adding zettel to %s's metadata, as no zettel was found.",
                page.file.src_path,
            )

        return enriched_page

    def get_zettels(self) -> list[Zettel]:
        return list(self.store.zettels)

    def get_zettel_by_path(self, path: Path) -> Zettel | None:
        """Delegate to store's lookup mechanism."""
        return self.store.get_by_path(path)

    def get_zettel_by_partial_path(self, partial_path: str) -> Zettel | None:
        """Delegate to store's lookup mechanism."""
        return self.store.get_by_partial_path(partial_path)
