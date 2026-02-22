from __future__ import annotations

import re
from typing import TYPE_CHECKING

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
            lines = path.read_text(encoding="utf-8-sig", errors="strict").splitlines()
        except OSError:
            return ""

        body_lines = self._skip_frontmatter(lines)

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

    @staticmethod
    def _skip_frontmatter(lines: list[str]) -> list[str]:
        """Skip YAML frontmatter delimited by --- lines."""
        divider_count = 0
        for i, line in enumerate(lines):
            if line.strip() == "---":
                divider_count += 1
                if divider_count == 2:
                    return lines[i + 1 :]
        return lines
