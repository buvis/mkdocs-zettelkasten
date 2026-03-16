from __future__ import annotations

from typing import TYPE_CHECKING

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
    extra_key: str | None = "workflow_enabled"

    def __init__(self) -> None:
        self._service = WorkflowService()
        self._dashboard: dict = {}

    def is_enabled(self, config: ZettelkastenConfig) -> bool:
        return config.workflow_enabled

    def compute(self, ctx: PipelineContext) -> None:
        self._dashboard = self._service.compute(
            ctx.store,
            ctx.backlinks,
            ctx.unlinked_mentions,
            timezone=ctx.config.timezone,
            fleeting_stale_days=ctx.config.fleeting_stale_days,
            review_stale_days=ctx.config.review_stale_days,
        )

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        self._service.configure(ctx.tags_folder, ctx.site_dir)
        self._service.generate(self._dashboard)
        self._service.add_to_build(files)
        config["extra"]["workflow_inbox_count"] = len(self._dashboard["inbox"])

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        pass
