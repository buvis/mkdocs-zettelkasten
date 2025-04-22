from typing import Any, Dict, List, Set

from mkdocs_zettelkasten.plugin.adapters.page_title import adapt_page_title
from mkdocs_zettelkasten.plugin.adapters.page_links_to_zettels import (
    adapt_page_links_to_zettels,
)
from mkdocs_zettelkasten.plugin.adapters.prev_next_page import get_prev_next_page
from mkdocs_zettelkasten.plugin.adapters.page_ref import get_page_ref


class PageTransformer:
    """
    Applies all Zettelkasten-specific transformations to page markdown.
    """

    def transform(
        self,
        markdown: str,
        page: Any,
        config: Dict[str, Any],
        files: List[Any],
        zettels: Set[str],
    ) -> str:
        """
        Apply all adapters to the markdown and update page navigation and references.
        """
        markdown = adapt_page_title(markdown, page, config, files)
        markdown = adapt_page_links_to_zettels(markdown, page, config, files, zettels)
        page.previous_page, page.next_page = get_prev_next_page(
            markdown, page, config, files, zettels
        )
        processed_md, page.ref = get_page_ref(markdown, page, config, files)
        return processed_md
