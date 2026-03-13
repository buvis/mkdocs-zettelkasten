from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.adapters.unlinked_mentions_to_page import (
    adapt_unlinked_mentions_to_page,
)
from mkdocs_zettelkasten.plugin.services.unlinked_mention_service import (
    UnlinkedMentionService,
)


class UnlinkedMentionFeature:
    name = "unlinked_mentions"
    depends_on: tuple[str, ...] = ()

    def __init__(self) -> None:
        self._service = UnlinkedMentionService()

    def is_enabled(self, config: ZettelkastenConfig) -> bool:  # noqa: ARG002
        return True

    def compute(self, ctx: PipelineContext) -> Any:
        return self._service.find_unlinked_mentions(ctx.store, ctx.link_map.resolved)

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        pass

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        adapt_unlinked_mentions_to_page(
            page, ctx.unlinked_mentions, ctx.store.get_by_id
        )
