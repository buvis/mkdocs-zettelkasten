from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.services.workflow_service import WorkflowService


class WorkflowFeature:
    name = "workflow"
    depends_on: tuple[str, ...] = ("backlinks", "unlinked_mentions")
    extra_key = "workflow_enabled"

    def __init__(self) -> None:
        self._service = WorkflowService()

    def is_enabled(self, config: ZettelkastenConfig) -> bool:
        return config.workflow_enabled

    def compute(self, ctx: PipelineContext) -> Any:
        self._service.configure(ctx.config.timezone, ctx.tags_folder, ctx.site_dir)
        return self._service.compute(
            ctx.store, ctx.backlinks, ctx.unlinked_mentions
        )

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        dashboard = ctx.results["workflow"]
        self._service.generate(dashboard)
        self._service.add_to_build(files)
        config["extra"]["workflow_inbox_count"] = len(dashboard["inbox"])

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        pass
