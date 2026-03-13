from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.services.validation_service import ValidationService


class ValidationFeature:
    name = "validation"
    depends_on: tuple[str, ...] = ("backlinks",)

    def __init__(self) -> None:
        self._service = ValidationService()

    def is_enabled(self, config: ZettelkastenConfig) -> bool:
        return config.validation_enabled

    def compute(self, ctx: PipelineContext) -> Any:
        self._service.validate(
            ctx.store,
            ctx.backlinks,
            ctx.invalid_files,
            ctx.link_map.broken,
            timezone=ctx.config.timezone,
        )
        return None

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        self._service.output_folder = ctx.tags_folder
        self._service.generate_report()
        self._service.add_to_build(files, config)
        config["extra"]["validation_issues_count"] = (
            self._service.total_actionable_issues()
        )

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:  # noqa: ARG002
        page.meta["validation_issues"] = self._service.get_issues(
            page.file.src_path
        )
