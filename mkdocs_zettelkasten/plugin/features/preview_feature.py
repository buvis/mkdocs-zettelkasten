from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.pipeline_context import export_json
from mkdocs_zettelkasten.plugin.services.preview_exporter import PreviewExporter


class PreviewFeature:
    name = "preview"
    depends_on: tuple[str, ...] = ()
    extra_key = "preview_enabled"

    def __init__(self) -> None:
        self._exporter = PreviewExporter()

    def is_enabled(self, config: ZettelkastenConfig) -> bool:
        return config.preview_enabled

    def compute(self, ctx: PipelineContext) -> Any:
        return self._exporter.export(ctx.store, file_suffix=ctx.config.file_suffix)

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        export_json(ctx, "previews.json", ctx.results["preview"], files, config)

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        pass
