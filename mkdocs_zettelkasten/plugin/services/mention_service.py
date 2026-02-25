from __future__ import annotations

import logging
import re
from collections import defaultdict

from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)

_MIN_TITLE_LEN = 3
_FENCED_CODE = re.compile(r"```.*?```", re.DOTALL)
_INLINE_CODE = re.compile(r"`[^`]+`")


class MentionService:
    """Detects unlinked mentions of zettel titles/IDs across the store."""

    def find_unlinked_mentions(self, store) -> dict[int, list[tuple[int, str]]]:
        """Return {target_id: [(source_id, snippet), ...]} for unlinked mentions."""
        mentions: dict[int, list[tuple[int, str]]] = defaultdict(list)

        for target in store.zettels:
            title = target.title
            title_ok = len(title) >= _MIN_TITLE_LEN
            id_str = str(target.id)
            title_pat = re.compile(r"\b" + re.escape(title) + r"\b", re.IGNORECASE) if title_ok else None
            id_pat = re.compile(r"\b" + re.escape(id_str) + r"\b")

            for source in store.zettels:
                if source.id == target.id:
                    continue
                if self._already_links_to(source, target):
                    continue

                body = source.body
                body_clean = _FENCED_CODE.sub(lambda m: " " * len(m.group()), body)

                for paragraph in self._split_paragraphs(body_clean):
                    stripped = self._strip_syntax(paragraph)

                    match = None
                    matched_term = None
                    if title_pat:
                        m = title_pat.search(stripped)
                        if m:
                            match = m
                            matched_term = title
                    if not match:
                        m = id_pat.search(stripped)
                        if m:
                            match = m
                            matched_term = id_str

                    if match:
                        # Get the original paragraph (before fenced code stripping)
                        # by finding the matching paragraph in the original body
                        orig_paragraph = self._find_original_paragraph(body, paragraph)
                        snippet = self._make_snippet(orig_paragraph, match, matched_term)
                        mentions[target.id].append((source.id, snippet))
                        break  # one mention per source is enough

        logger.debug("Found unlinked mentions for %d targets", len(mentions))
        return dict(mentions)

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

    @staticmethod
    def _find_original_paragraph(original_body: str, cleaned_paragraph: str) -> str:
        """Find the original paragraph text before code-block stripping."""
        # The cleaned paragraph has fenced code blocks replaced with spaces.
        # Find a paragraph in the original body at the same position.
        # Since we split by blank lines, we can match by position.
        orig_paragraphs = []
        current: list[str] = []
        for line in original_body.splitlines():
            if line.strip() == "":
                if current:
                    orig_paragraphs.append("\n".join(current))
                    current = []
            else:
                current.append(line)
        if current:
            orig_paragraphs.append("\n".join(current))

        # The cleaned body may have merged paragraphs differently due to
        # fenced code removal, but in practice the paragraph count should match
        # because fenced code blocks are replaced with same-length spaces
        # (preserving newlines structure). Just find the paragraph whose
        # length matches.
        for orig in orig_paragraphs:
            if len(orig) == len(cleaned_paragraph):
                return orig

        return cleaned_paragraph

    @staticmethod
    def _make_snippet(paragraph: str, match: re.Match, term: str) -> str:
        """Create a display snippet with <mark> around the matched term."""
        # Clean link syntax for display: replace links with their display text
        clean = WIKI_LINK.sub(lambda m: m.group("title") or m.group("url"), paragraph)
        clean = MD_LINK.sub(lambda m: m.group("title"), clean)

        # Find the term in the cleaned text and insert <mark>
        term_pat = re.compile(r"\b" + re.escape(term) + r"\b", re.IGNORECASE)
        m = term_pat.search(clean)
        if m:
            clean = clean[:m.start()] + "<mark>" + clean[m.start():m.end()] + "</mark>" + clean[m.end():]
            mark_start = m.start()
        else:
            mark_start = 0

        # Flatten to single line for display
        clean = " ".join(clean.split())

        if len(clean) <= 200:
            return clean

        # Center a 200-char window on the match
        half = 100
        start = max(0, mark_start - half)
        end = min(len(clean), mark_start + len("<mark>") + len(term) + len("</mark>") + half)

        if start > 0:
            space = clean.rfind(" ", 0, start)
            start = space + 1 if space != -1 else start
        if end < len(clean):
            space = clean.find(" ", end)
            end = space if space != -1 else end

        snippet = clean[start:end]
        if start > 0:
            snippet = "..." + snippet
        if end < len(clean):
            snippet = snippet + "..."
        return snippet
