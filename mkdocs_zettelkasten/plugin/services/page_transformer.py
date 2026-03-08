import logging

from mkdocs.config.defaults import MkDocsConfig
from mkdocs.structure.files import Files
from mkdocs.structure.pages import Page

from mkdocs_zettelkasten.plugin.adapters.backlinks_to_page import (
    adapt_backlinks_to_page,
)
from mkdocs_zettelkasten.plugin.adapters.page_links_to_zettels import (
    adapt_page_links_to_zettels,
)
from mkdocs_zettelkasten.plugin.adapters.page_ref import get_page_ref
from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title
from mkdocs_zettelkasten.plugin.adapters.prev_next_page import get_prev_next_page
from mkdocs_zettelkasten.plugin.adapters.sequence_to_page import (
    adapt_sequence_to_page,
)
from mkdocs_zettelkasten.plugin.adapters.suggestions_to_page import (
    adapt_suggestions_to_page,
)
from mkdocs_zettelkasten.plugin.adapters.transclusion import adapt_transclusion
from mkdocs_zettelkasten.plugin.adapters.unlinked_mentions_to_page import (
    adapt_unlinked_mentions_to_page,
)
from mkdocs_zettelkasten.plugin.services.zettel_service import ZettelService

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class PageTransformer:
    """
    Applies all Zettelkasten-specific transformations to page markdown.

    Adapter execution order (dependency DAG):
        1. add_zettel_to_page     — no prerequisites; populates page.meta["zettel"]
        2. adapt_page_title       — requires: zettel in page.meta
        3. adapt_transclusion     — no prerequisites; expands transclusions in markdown
        4. adapt_page_links       — requires: transclusions resolved (step 3)
        5. get_page_ref           — requires: links resolved (step 4)
        6. get_prev_next_page     — no prerequisites; independent navigation
        7. adapt_backlinks        — requires: zettel in page.meta (step 1)
        8. adapt_unlinked_mentions— requires: zettel in page.meta (step 1)
        9. adapt_suggestions      — requires: zettel in page.meta (step 1)
       10. adapt_sequence         — requires: zettel in page.meta (step 1)
    """

    def transform(
        self,
        markdown: str,
        page: Page,
        config: MkDocsConfig,
        files: Files,
        zettel_service: ZettelService,
    ) -> str:
        """
        Apply all adapters to the markdown and update references.
        """
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
        # Step 7 — requires: zettel in page.meta (step 1)
        _run(
            "adapt_backlinks_to_page",
            adapt_backlinks_to_page,
            page,
            zettel_service.backlinks,
            zettel_service.get_zettel_by_id,
            file_suffix=zettel_service.file_suffix,
        )
        # Step 8 — requires: zettel in page.meta (step 1)
        _run(
            "adapt_unlinked_mentions_to_page",
            adapt_unlinked_mentions_to_page,
            page,
            zettel_service.unlinked_mentions,
            zettel_service.get_zettel_by_id,
        )
        # Step 9 — requires: zettel in page.meta (step 1)
        _run(
            "adapt_suggestions_to_page",
            adapt_suggestions_to_page,
            page,
            zettel_service.suggestions,
            zettel_service.get_zettel_by_id,
            file_suffix=zettel_service.file_suffix,
        )
        # Step 10 — requires: zettel in page.meta (step 1)
        _run(
            "adapt_sequence_to_page",
            adapt_sequence_to_page,
            page,
            zettel_service.sequence_children,
            zettel_service.get_zettel_by_id,
            file_suffix=zettel_service.file_suffix,
        )

        logger.debug("Finished %s transformations", src)
        return processed_md
