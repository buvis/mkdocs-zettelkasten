from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext

from mkdocs_zettelkasten.plugin.adapters.suggestions_to_page import (
    adapt_suggestions_to_page,
)
from mkdocs_zettelkasten.plugin.pipeline_context import export_json
from mkdocs_zettelkasten.plugin.services.suggestion_service import SuggestionService


class SuggestionFeature:
    name = "suggestions"
    depends_on: tuple[str, ...] = ()
    extra_key: str | None = None

    def __init__(self) -> None:
        self._service = SuggestionService()
        self._suggestions: dict[int, list[dict]] = {}

    def is_enabled(self, config: ZettelkastenConfig) -> bool:
        return config.suggestions_enabled

    def compute(self, ctx: PipelineContext) -> None:
        self._suggestions = self._service.compute(
            ctx.store, ctx.tags_metadata, ctx.link_map.resolved
        )

    def export(self, ctx: PipelineContext, files: Files, config: MkDocsConfig) -> None:
        sugg_data: dict[str, list[dict]] = {}
        store = ctx.store
        suffix = ctx.config.file_suffix
        for zid, suggs in self._suggestions.items():
            z = store.get_by_id(zid)
            if not z:
                continue
            entries = []
            for s in suggs:
                target = store.get_by_id(s["target_id"])
                if not target:
                    continue
                entries.append(
                    {
                        "target_id": str(s["target_id"]),
                        "target_title": target.title,
                        "target_url": target.rel_path.removesuffix(suffix) + "/",
                        "reason": s["reason"],
                        "confidence": s["confidence"],
                    }
                )
            if entries:
                sugg_data[str(zid)] = entries

        export_json(ctx, "suggestions.json", sugg_data, files, config)

    def adapt_page(self, page: Page, ctx: PipelineContext) -> None:
        adapt_suggestions_to_page(
            page,
            self._suggestions,
            ctx.store.get_by_id,
            file_suffix=ctx.config.file_suffix,
        )
