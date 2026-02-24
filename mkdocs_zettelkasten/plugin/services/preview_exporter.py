from __future__ import annotations

import re
from typing import TYPE_CHECKING

from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter

if TYPE_CHECKING:
    from pathlib import Path

    from mkdocs_zettelkasten.plugin.services.zettel_store import ZettelStore


class PreviewExporter:
    """Exports zettel preview data as a JSON-serializable dict."""

    MAX_EXCERPT_LENGTH = 200

    def export(
        self,
        store: ZettelStore,
        file_suffix: str = ".md",
    ) -> dict:
        previews = {}

        for z in store.zettels:
            zid = str(z.id)
            url = z.rel_path.removesuffix(file_suffix) + "/"
            excerpt = self._extract_excerpt(z.path)
            previews[zid] = {"title": z.title, "excerpt": excerpt, "url": url}

        return previews

    def _extract_excerpt(self, path: Path) -> str:
        """Read zettel file, skip YAML frontmatter, return first paragraph."""
        try:
            content = path.read_text(encoding="utf-8-sig", errors="strict")
        except OSError:
            return ""

        _, body = parse_frontmatter(content)
        body_lines = body.splitlines()

        paragraph_lines: list[str] = []
        for line in body_lines:
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
        if len(text) > self.MAX_EXCERPT_LENGTH:
            text = text[: self.MAX_EXCERPT_LENGTH].rsplit(" ", 1)[0] + "\u2026"
        return text

