from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

from .backlink_processor import BacklinkProcessor
from .zettel_parser import ZettelParser
from .zettel_store import ZettelStore


class ZettelService:
    """Orchestrates zettel processing pipeline."""

    def __init__(self) -> None:
        self.store = ZettelStore()
        self.backlinks: dict[str, list[Zettel]] = {}

    def process_files(self, files: Files) -> None:
        """Main processing pipeline."""
        valid_zettels, _ = ZettelParser.parse_files(files)
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
        else:
            enriched_page.meta["is_zettel"] = False

        return enriched_page

    def get_zettels(self) -> list[Zettel]:
        return list(self.store.zettels)

    def get_zettel_by_path(self, path: Path) -> Zettel | None:
        """Delegate to store's lookup mechanism."""
        return self.store.get_by_path(path)

    def get_zettel_by_partial_path(self, partial_path: str) -> Zettel | None:
        """Delegate to store's lookup mechanism."""
        return self.store.get_by_partial_path(partial_path)
