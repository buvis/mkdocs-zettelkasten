from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

import logging

from .backlink_processor import BacklinkProcessor
from .mention_service import MentionService
from .sequence_service import SequenceService
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
        self.invalid_files: list = []
        self.zettel_config: dict[str, Any] = {}
        self.file_suffix: str = ".md"
        self.mention_service = MentionService()
        self.mentions: dict[int, list[tuple[int, str]]] = {}
        self.sequence_children: dict[int, list[int]] = {}

    def configure(self, zettel_config: dict[str, Any]) -> None:
        self.zettel_config = zettel_config
        self.file_suffix = zettel_config.get("file_suffix", ".md")

    def process_files(self, files: Files, config: MkDocsConfig) -> None:
        """Main processing pipeline."""
        docs_dir = config["docs_dir"]
        logger.info("Scanning `%s` for zettels", docs_dir)
        valid_zettels, self.invalid_files = ZettelParser.parse_files(
            files, self.zettel_config
        )
        logger.info("Found %s zettels in `%s`", len(valid_zettels), docs_dir)
        self.store.update(valid_zettels)
        self.backlinks = BacklinkProcessor.process(
            self.store, file_suffix=self.file_suffix
        )
        self.mentions = self.mention_service.find_unlinked_mentions(self.store)
        self.sequence_children = SequenceService.build_tree(self.store)

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

    def get_zettel_by_id(self, zettel_id: int) -> Zettel | None:
        """Look up zettel by ID."""
        return self.store.get_by_id(zettel_id)

    def get_zettel_by_partial_path(self, partial_path: str) -> Zettel | None:
        """Delegate to store's lookup mechanism."""
        return self.store.get_by_partial_path(partial_path)
