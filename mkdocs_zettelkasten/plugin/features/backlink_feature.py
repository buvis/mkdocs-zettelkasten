from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.adapters.backlinks_to_page import (
    adapt_backlinks_to_page,
)
from mkdocs_zettelkasten.plugin.services.backlink_processor import BacklinkProcessor


class BacklinkFeature:
    name = "backlinks"
    depends_on: tuple[str, ...] = ()
    extra_key: str | None = None

    def is_enabled(self, config: ZettelkastenConfig) -> bool:  # noqa: ARG002
        return True

    def compute(self, ctx: PipelineContext) -> None:
        ctx.backlinks = BacklinkProcessor.process(ctx.store, ctx.link_map.resolved)

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        pass

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        adapt_backlinks_to_page(
            page,
            ctx.backlinks,
            ctx.store.get_by_id,
            file_suffix=ctx.config.file_suffix,
        )
