from __future__ import annotations

import logging
import re
from collections import defaultdict

from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK
from mkdocs_zettelkasten.plugin.utils.snippet_utils import truncate_around

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)

_MIN_TITLE_LEN = 3
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")


class UnlinkedMentionService:
    """Detects unlinked mentions of zettel titles/IDs across the store."""

    def find_unlinked_mentions(self, store) -> dict[int, list[tuple[int, str]]]:
        """Return {target_id: [(source_id, snippet), ...]} for unlinked mentions."""
        mentions: dict[int, list[tuple[int, str]]] = defaultdict(list)

        for target in store.zettels:
            title = target.title
            id_str = str(target.id)
            title_pat = (
                re.compile(r"\b" + re.escape(title) + r"\b", re.IGNORECASE)
                if len(title) >= _MIN_TITLE_LEN
                else None
            )
            id_pat = re.compile(r"\b" + re.escape(id_str) + r"\b")

            for source in store.zettels:
                if source.id == target.id or self._already_links_to(source, target):
                    continue
                result = self._find_mention_in_body(
                    source.body, title_pat, title, id_pat, id_str
                )
                if result:
                    mentions[target.id].append((source.id, result))

        logger.debug("Found unlinked mentions for %d targets", len(mentions))
        return dict(mentions)

    def _find_mention_in_body(self, body, title_pat, title, id_pat, id_str):
        """Search body paragraphs for a mention, return snippet or None."""
        body_clean = _FENCED_CODE.sub(lambda m: " " * len(m.group()), body)

        for paragraph in self._split_paragraphs(body_clean):
            stripped = self._strip_syntax(paragraph)
            matched_term = self._match_paragraph(
                stripped, title_pat, title, id_pat, id_str
            )
            if matched_term:
                orig_paragraph = self._find_original_paragraph(body, paragraph)
                return self._make_snippet(orig_paragraph, matched_term)
        return None

    @staticmethod
    def _match_paragraph(stripped, title_pat, title, id_pat, id_str):
        """Return matched term if paragraph contains a mention, else None."""
        if title_pat and title_pat.search(stripped):
            return title
        if id_pat.search(stripped):
            return id_str
        return None

    @staticmethod
    def _already_links_to(source, target) -> bool:
        target_id = str(target.id)
        return any(link.removesuffix(".md") == target_id for link in source.links)

    @staticmethod
    def _strip_syntax(text: str) -> str:
        """Replace wiki links, md links, and inline code with spaces (preserving length)."""
        result = text
        for pat in (WIKI_LINK, MD_LINK, _INLINE_CODE):
            result = pat.sub(lambda m: " " * len(m.group()), result)
        return result

    @staticmethod
    def _split_paragraphs(body: str) -> list[str]:
        """Split body into paragraphs by blank lines."""
        paragraphs = []
        current: list[str] = []
        for line in body.splitlines():
            if line.strip() == "":
                if current:
                    paragraphs.append("\n".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            paragraphs.append("\n".join(current))
        return paragraphs

    def _find_original_paragraph(
        self, original_body: str, cleaned_paragraph: str
    ) -> str:
        """Find the original paragraph text before code-block stripping."""
        orig_paragraphs = self._split_paragraphs(original_body)
        cleaned_paragraphs = self._split_paragraphs(
            _FENCED_CODE.sub(lambda m: " " * len(m.group()), original_body)
        )

        for i, cp in enumerate(cleaned_paragraphs):
            if cp == cleaned_paragraph and i < len(orig_paragraphs):
                return orig_paragraphs[i]

        return cleaned_paragraph

    @staticmethod
    def _make_snippet(paragraph: str, term: str) -> str:
        """Create a display snippet with <mark> around the matched term."""
        clean = WIKI_LINK.sub(lambda m: m.group("title") or m.group("url"), paragraph)
        clean = MD_LINK.sub(lambda m: m.group("title"), clean)

        term_pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        m = term_pat.search(clean)
        if m:
            marked = f"<mark>{clean[m.start() : m.end()]}</mark>"
            clean = clean[: m.start()] + marked + clean[m.end() :]
            mark_start = m.start()
            marker_len = len(marked)
        else:
            mark_start = 0
            marker_len = 0

        clean = " ".join(clean.split())
        return truncate_around(clean, mark_start, marker_len)
