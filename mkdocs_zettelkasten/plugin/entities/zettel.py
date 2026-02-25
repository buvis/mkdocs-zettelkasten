from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from pathlib import Path

import logging
from zoneinfo import ZoneInfo

import yaml
from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date
from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter
from mkdocs_zettelkasten.plugin.utils.git_utils import GitUtil
from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class ZettelFormatError(ValueError):
    """Exception raised for invalid zettel file format"""


class Zettel:
    _MOC_ROLES = frozenset({"moc", "index", "hub", "structure"})

    def __init__(
        self,
        abs_src_path: Path,
        src_path: str,
        zettel_config: dict[str, Any] | None = None,
    ) -> None:
        self.id: int = 0
        self.title: str = ""
        self.path: Path = abs_src_path
        self.rel_path: str = src_path
        self.backlinks: list[dict[str, str]] = []
        self.links: list[str] = []
        self.last_update_date: str = ""
        self.note_type: str | None = None
        self.maturity: str | None = None
        self.source: str | None = None
        self.role: str | None = None
        self.moc_parents: list[dict[str, str]] = []
        self.link_snippets: dict[str, str] = {}
        self.body: str = ""
        self.unlinked_mentions: list[dict[str, str]] = []
        self.sequence_parent_id: int | None = None
        self.sequence_parent: dict[str, str] | None = None
        self.sequence_children: list[dict[str, str]] = []
        self.sequence_breadcrumb: list[dict[str, str]] = []
        self.sequence_tree: list[dict] = []

        cfg = zettel_config or {}
        self._id_key = cfg.get("id_key", "id")
        self._date_key = cfg.get("date_key", "date")
        self._last_update_key = cfg.get("last_update_key", "last_update")
        self._type_key = cfg.get("type_key", "type")
        self._maturity_key = cfg.get("maturity_key", "maturity")
        self._role_key = cfg.get("role_key", "role")
        self._sequence_key = cfg.get("sequence_key", "sequence")
        self._id_format = cfg.get("id_format", r"^\d{14}$")
        self._tz = cfg.get("timezone") or ZoneInfo("UTC")
        self._date_format = cfg.get("date_format", "%Y-%m-%d")

        self._initialize_zettel()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Zettel) and self.id == other.id

    @property
    def is_moc(self) -> bool:
        return self.role in self._MOC_ROLES

    def _initialize_zettel(self) -> None:
        """Orchestrates the zettel initialization process."""
        try:
            content = self.path.read_text(encoding="utf-8-sig", errors="strict")
        except OSError as err:
            logger.exception("Failed to read file %s", self.path)
            msg = f"File {self.path} read error"
            raise ZettelFormatError(msg) from err

        header_text, body_text = parse_frontmatter(content)
        if not header_text:
            logger.error("Unclosed YAML header in file: %s", self.path)
            msg = "Unclosed YAML header in file"
            raise ZettelFormatError(msg)

        meta = self._parse_metadata(header_text)
        self.body = body_text
        body_lines = body_text.splitlines()
        self._extract_links(body_lines)
        self._set_core_metadata(meta, self._find_alt_title(body_lines))
        self._set_optional_metadata(meta)
        logger.debug(
            "Initialized zettel %s (ID: %s, Title: %s)",
            self.rel_path,
            self.id,
            self.title,
        )

    def _parse_metadata(self, header: str) -> dict:
        """Parses YAML metadata from header text."""
        try:
            meta = yaml.safe_load(header) or {}

            if not isinstance(meta, dict):
                logger.error(
                    "Invalid YAML structure in %s: not a dictionary", self.path
                )
                msg = "Invalid YAML structure"
                raise ZettelFormatError(msg)

            logger.debug("Found metadata keys: %s", list(meta.keys()))

        except (ScannerError, AttributeError) as err:
            logger.exception("Failed to parse YAML in %s", self.path)
            msg = f"Invalid YAML in {self.path}"
            raise ZettelFormatError(msg) from err
        else:
            return meta

    def _find_alt_title(self, body: list[str]) -> str:
        """Finds alternative title from markdown heading."""
        for line in body:
            if line.lstrip().startswith("# "):
                return line.strip()[2:]
        return ""

    def _extract_links(self, body: list[str]) -> None:
        """Extracts all wiki and markdown links from body."""
        wiki_count = 0
        md_count = 0

        for paragraph in self._split_paragraphs(body):
            for m in WIKI_LINK.finditer(paragraph):
                url = m.group("url")
                self.links.append(url)
                wiki_count += 1
                if url not in self.link_snippets:
                    self.link_snippets[url] = self._make_snippet(paragraph, m)

            for m in MD_LINK.finditer(paragraph):
                url = m.group("url")
                self.links.append(url)
                md_count += 1
                if url not in self.link_snippets:
                    self.link_snippets[url] = self._make_snippet(paragraph, m)

        logger.debug(
            "Extracted %d wiki links and %d markdown links",
            wiki_count,
            md_count,
        )

    @staticmethod
    def _split_paragraphs(body: list[str]) -> list[str]:
        """Joins body lines into paragraph strings split by blank lines."""
        paragraphs: list[str] = []
        current: list[str] = []
        for line in body:
            if line.strip() == "":
                if current:
                    paragraphs.append(" ".join(current))
                    current = []
            else:
                current.append(line.strip())
        if current:
            paragraphs.append(" ".join(current))
        return paragraphs

    @staticmethod
    def _make_snippet(paragraph: str, match: re.Match) -> str:
        """Cleans link syntax and trims paragraph to ~200 chars around the link."""
        # Replace the matched link with its display text wrapped in <mark>
        link_text = match.group("title") or match.group("url")
        marked_text = f"<mark>{link_text}</mark>"
        clean = paragraph[:match.start()] + marked_text + paragraph[match.end():]
        # Strip remaining link syntax
        clean = WIKI_LINK.sub(lambda m: m.group("title") or m.group("url"), clean)
        clean = MD_LINK.sub(lambda m: m.group("title"), clean)

        link_pos = match.start()

        if len(clean) <= 200:
            return clean

        # Center a 200-char window on the link
        half = 100
        start = max(0, link_pos - half)
        end = min(len(clean), link_pos + len(marked_text) + half)

        # Expand to word boundaries
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

    def _set_core_metadata(self, meta: dict, alt_title: str) -> None:
        """Sets fundamental metadata fields."""
        if not meta.get(self._id_key):
            logger.error("Missing required ID in zettel: %s", self.path)
            msg = "Missing zettel ID"
            raise ZettelFormatError(msg)

        self.id = meta[self._id_key]

        if meta.get("title"):
            self.title = meta["title"]
        elif alt_title:
            self.title = alt_title
        else:
            self.title = self._generate_filename_title()

        self._determine_last_update_date(meta)

    def _set_optional_metadata(self, meta: dict) -> None:
        raw_type = meta.get(self._type_key)
        self.note_type = str(raw_type) if raw_type is not None else None
        raw_maturity = meta.get(self._maturity_key)
        self.maturity = str(raw_maturity) if raw_maturity is not None else None
        raw_source = meta.get("source")
        self.source = str(raw_source) if raw_source is not None else None
        raw_role = meta.get(self._role_key)
        self.role = str(raw_role) if raw_role is not None else None
        raw_seq = meta.get(self._sequence_key)
        self.sequence_parent_id = int(raw_seq) if raw_seq is not None else None

    def _generate_filename_title(self) -> str:
        """Generates title from filename using pattern matching."""
        stem = self.path.stem
        # Strip ID prefix from filename (remove anchors from id_format pattern)
        id_prefix = self._id_format.lstrip("^").rstrip("$")
        clean_stem = re.sub(id_prefix, "", stem)
        return clean_stem.replace("_", " ").replace("-", " ").strip().capitalize()

    def _determine_last_update_date(self, meta: dict) -> None:
        """Determines most recent valid date from multiple sources."""
        candidate_date = self._get_initial_candidate_date(meta)
        revision_date = self._get_revision_date()

        if self._last_update_key in meta:
            final_date = candidate_date
        else:
            final_date = max(candidate_date, revision_date, key=lambda d: d.timestamp())
            logger.debug(
                "Using later date between metadata (%s) and modification (%s) for %s",
                candidate_date.strftime("%Y-%m-%d"),
                revision_date.strftime("%Y-%m-%d"),
                self.rel_path,
            )

        self.last_update_date = final_date.strftime(self._date_format)

    def _get_initial_candidate_date(self, meta: dict) -> datetime.datetime:
        """Gets first valid date from metadata sources."""
        for field in [self._last_update_key, self._date_key]:
            if date := convert_string_to_date(meta.get(field, ""), tz=self._tz):
                return date

        id_date = convert_string_to_date(str(self.id), tz=self._tz)
        if id_date:
            return id_date

        return datetime.datetime.now(tz=self._tz)

    def _get_revision_date(self) -> datetime.datetime:
        """Gets revision date from VCS or filesystem."""
        if GitUtil.is_tracked(str(self.path)):
            git_date = GitUtil().get_revision_date_for_file(str(self.path))
            if git_date is not None:
                return git_date

        return self._get_mtime()

    def _get_mtime(self) -> datetime.datetime:
        """Gets modification time from filesystem."""
        st_mtime = self.path.stat().st_mtime
        return datetime.datetime.fromtimestamp(st_mtime, tz=self._tz)
