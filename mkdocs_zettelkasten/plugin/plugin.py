from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

from mkdocs.plugins import BasePlugin

from mkdocs_zettelkasten.plugin.services.page_transformer import PageTransformer
from mkdocs_zettelkasten.plugin.services.tags_service import TagsService
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService


# reference: https://www.mkdocs.org/dev-guide/plugins
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

    def on_config(self, config: MkDocsConfig) -> None:
        self.tags_service.configure(config)

    def on_files(self, files: Files, config: MkDocsConfig) -> None:
        _ = config
        self.zettel_service.process_files(files)
        self.tags_service.process_files(files)

    def on_page_markdown(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
    ) -> str | None:
        return self.page_transformer.transform(
            markdown,
            page,
            config,
            files,
            self.zettel_service,
        )
