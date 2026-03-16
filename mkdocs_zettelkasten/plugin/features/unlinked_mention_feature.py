from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.services.unlinked_mention_service import (
    UnlinkedMentionService,
)


class UnlinkedMentionFeature:
    name = "unlinked_mentions"
    depends_on: tuple[str, ...] = ()
    extra_key: str | None = None

    def __init__(self) -> None:
        self._service = UnlinkedMentionService()

    def is_enabled(self, config: ZettelkastenConfig) -> bool:  # noqa: ARG002
        return True

    def compute(self, ctx: PipelineContext) -> None:
        ctx.unlinked_mentions = self._service.find_unlinked_mentions(
            ctx.store,
            ctx.link_map.resolved,
            min_title_len=ctx.config.min_mention_title_length,
        )

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        pass

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        pass
