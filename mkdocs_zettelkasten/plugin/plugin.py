from __future__ import annotations
from typing import Any, Dict, List

from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File
from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService
from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer


class ZettelkastenPlugin(BasePlugin):
    """
    MkDocs plugin entrypoint for Zettelkasten features.
    Orchestrates tag generation, zettel management, and page adaptation.
    """

    def __init__(self) -> None:
        super().__init__()
        self.tags_service = TagsService()
        self.zettel_service = ZettelService()
        self.page_transformer = PageTransformer()

    def on_config(self, config: Dict[str, Any]) -> None:
        self.tags_service.configure(config)

    def on_files(self, files: List[File], config: Dict[str, Any]) -> None:
        self.zettel_service.process_files(files, config)
        self.tags_service.process_metadata(files, config)
        self.tags_service.generate_tags_file()
        self.tags_service.add_tags_file_to_build(files, config)

    def on_page_markdown(
        self, markdown: str, page: Page, config: Dict[str, Any], files: List[File]
    ) -> str:
        return self.page_transformer.transform(
            markdown, page, config, files, self.zettel_service.zettels
        )
