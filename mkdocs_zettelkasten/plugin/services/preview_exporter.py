from __future__ import annotations

import logging
import re
from typing import TYPE_CHECKING

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)

if TYPE_CHECKING:
    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


class PreviewExporter:
    """Exports zettel preview data as a JSON-serializable dict."""

    def export(
        self,
        store: ZettelStore,
        file_suffix: str = ".md",
        *,
        max_excerpt_length: int = 200,
    ) -> dict:
        previews = {}

        for z in store.zettels:
            zid = str(z.id)
            url = z.rel_path.removesuffix(file_suffix) + "/"
            excerpt = self._extract_excerpt(z.body, max_excerpt_length)
            previews[zid] = {"title": z.title, "excerpt": excerpt, "url": url}

        return previews

    def _extract_excerpt(self, body: str, max_length: int) -> str:
        """Extract first paragraph from zettel body text."""
        paragraph_lines: list[str] = []
        for line in body.splitlines():
            stripped = line.strip()
            if not stripped:
                if paragraph_lines:
                    break
                continue
            if stripped.startswith("#"):
                if paragraph_lines:
                    break
                continue
            paragraph_lines.append(stripped)

        text = " ".join(paragraph_lines)
        text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
        text = re.sub(r"\[\[(?:[^|\]]+\|)?([^\]]+)\]\]", r"\1", text)
        if len(text) > max_length:
            text = text[:max_length].rsplit(" ", 1)[0] + "\u2026"
        return text
