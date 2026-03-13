from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.services.outline_service import OutlineService


class OutlineFeature:
    name = "outline"
    depends_on: tuple[str, ...] = ("sequence_children",)
    extra_key: str | None = None

    def __init__(self) -> None:
        self._service = OutlineService()
        self._outlines: dict = {}

    def is_enabled(self, config: ZettelkastenConfig) -> bool:  # noqa: ARG002
        return True

    def compute(self, ctx: PipelineContext) -> None:
        self._outlines = self._service.compute(
            ctx.store,
            ctx.sequence_children,
            file_suffix=ctx.config.file_suffix,
        )

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        self._service.configure(ctx.tags_folder, ctx.site_dir)
        if self._outlines["moc_outlines"] or self._outlines["sequence_outlines"]:
            self._service.generate(self._outlines)
            self._service.add_to_build(files)
            config["extra"]["outline_enabled"] = True

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        pass
