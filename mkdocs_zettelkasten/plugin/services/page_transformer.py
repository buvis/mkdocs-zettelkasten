from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from mkdocs.config.defaults import MkDocsConfig
    from mkdocs.structure.files import Files
    from mkdocs.structure.pages import Page

    from mkdocs_zettelkasten.plugin.feature import Feature
    from mkdocs_zettelkasten.plugin.pipeline_context import PipelineContext
    from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

from mkdocs_zettelkasten.plugin.adapters.page_links_to_zettels import (
    adapt_page_links_to_zettels,
)
from mkdocs_zettelkasten.plugin.adapters.page_ref import get_page_ref
from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title
from mkdocs_zettelkasten.plugin.adapters.prev_next_page import get_prev_next_page
from mkdocs_zettelkasten.plugin.adapters.transclusion import adapt_transclusion

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class PageTransformer:
    """
    Applies all Zettelkasten-specific transformations to page markdown.

    Core adapter execution order (dependency DAG):
        1. add_zettel_to_page     — no prerequisites; populates page.meta["zettel"]
        2. adapt_page_title       — requires: zettel in page.meta
        3. adapt_transclusion     — no prerequisites; expands transclusions in markdown
        4. adapt_page_links       — requires: transclusions resolved (step 3)
        5. get_page_ref           — requires: links resolved (step 4)
        6. get_prev_next_page     — no prerequisites; independent navigation

    After core adapters, feature.adapt_page() is called for each active feature.
    """

    def transform(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
        zettel_service: ZettelService,
        features: list[Feature],
        ctx: PipelineContext,
    ) -> str:
        """Apply core adapters and feature adapters to the markdown."""
        src = page.file.src_path
        logger.debug("Started %s transformations", src)

        def _run(name: str, fn, *args, **kwargs):
            try:
                return fn(*args, **kwargs)
            except Exception:
                logger.exception("Adapter %s failed on %s", name, src)
                raise

        # Step 1 — no prerequisites; populates page.meta["zettel"]
        page = _run("add_zettel_to_page", zettel_service.add_zettel_to_page, page)
        # Step 2 — requires: zettel in page.meta (step 1)
        markdown = _run(
            "adapt_page_title",
            adapt_page_title,
            markdown,
            page,
            page.meta.get("zettel"),
        )
        # Step 3 — no prerequisites; expands transclusions before link processing
        markdown = _run(
            "adapt_transclusion",
            adapt_transclusion,
            markdown,
            zettel_service.get_zettel_by_partial_path,
            site_url=config["site_url"],
            file_suffix=zettel_service.file_suffix,
            strip_heading=config.get("extra", {}).get(
                "transclusion_strip_heading", True
            ),
        )
        # Step 4 — requires: transclusions resolved (step 3)
        markdown = _run(
            "adapt_page_links_to_zettels",
            adapt_page_links_to_zettels,
            markdown,
            page,
            config,
            files,
            zettel_service.get_zettel_by_partial_path,
            file_suffix=zettel_service.file_suffix,
        )
        # Step 5 — requires: links resolved (step 4)
        processed_md, page.meta["ref"] = _run(
            "get_page_ref", get_page_ref, markdown, page, config
        )
        # Step 6 — no prerequisites; independent navigation lookup
        page.previous_page, page.next_page = _run(
            "get_prev_next_page",
            get_prev_next_page,
            page,
            files,
            zettel_service.get_zettels(),
            file_suffix=zettel_service.file_suffix,
        )

        # Feature adapters
        for feature in features:
            _run(feature.name, feature.adapt_page, page, ctx)

        logger.debug("Finished %s transformations", src)
        return processed_md
