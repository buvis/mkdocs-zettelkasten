from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

import logging

import tzlocal
import yaml
from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date
from mkdocs_zettelkasten.plugin.utils.git_utils import GitUtil
from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK


logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class ZettelFormatError(ValueError):
    """Exception raised for invalid zettel file format"""


class Zettel:
    COUNT_HEADER_DIVIDERS = 2
    MARK_DIVIDER = "---"

    def __init__(
        self,
        abs_src_path: Path,
        src_path: str,
        zettel_config: dict[str, str] | None = None,
    ) -> None:
        self.id: int = 0
        self.title: str = ""
        self.path: Path = abs_src_path
        self.rel_path: str = src_path
        self.backlinks: list[dict[str, str]] = []
        self.links: list[str] = []
        self.last_update_date: str = ""

        cfg = zettel_config or {}
        self._id_key = cfg.get("id_key", "id")
        self._date_key = cfg.get("date_key", "date")
        self._last_update_key = cfg.get("last_update_key", "last_update")
        self._id_format = cfg.get("id_format", r"^\d{14}$")
        self._tz = cfg.get("timezone") or tzlocal.get_localzone()

        self._initialize_zettel()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Zettel) and self.id == other.id

    def _initialize_zettel(self) -> None:
        """Orchestrates the zettel initialization process."""
        header, body = self._read_header_and_body()
        meta = self._parse_metadata(header)
        self._extract_links(body)
        self._set_core_metadata(meta, self._find_alt_title(body))
        logger.info("Successfully initialized zettel %s (ID: %s, Title: %s)",
                   self.rel_path, self.id, self.title)

    def _read_header_and_body(self) -> tuple[list[str], list[str]]:
        """Reads and separates YAML header from markdown body."""
        header = []
        body = []
        read_state = ReadState()

        try:
            with self.path.open(encoding="utf-8-sig", errors="strict") as file:
                for line in file:
                    self._process_line(line, read_state, header, body)
        except OSError as err:
            logger.exception("Failed to read file %s", self.path)
            msg = f"File {self.path} read error"
            raise ZettelFormatError(msg) from err

        self._validate_header(read_state)
        return header, body

    def _validate_header(self, read_state: ReadState) -> None:
        """Validate header termination."""
        if read_state.divider_count < Zettel.COUNT_HEADER_DIVIDERS:
            logger.error("Unclosed YAML header in file: %s", self.path)
            msg = "Unclosed YAML header in file"
            raise ZettelFormatError(msg)

    def _process_line(
        self,
        line: str,
        state: ReadState,
        header: list[str],
        body: list[str],
    ) -> None:
        """Processes a single line based on current read state."""
        if line.strip() == "---":
            state.handle_divider()
            return

        if state.is_reading_header:
            header.append(line)
        elif state.is_reading_body:
            body.append(line)

    def _parse_metadata(self, header: list[str]) -> dict:
        """Parses YAML metadata from header lines."""
        try:
            meta = yaml.safe_load("".join(header)) or {}

            if not isinstance(meta, dict):
                logger.error("Invalid YAML structure in %s: not a dictionary", self.path)
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
        wiki_links = []
        markdown_links = []

        for line in body:
            wiki_matches = [m.groupdict()["url"] for m in WIKI_LINK.finditer(line)]
            md_matches = [m.groupdict()["url"] for m in MD_LINK.finditer(line)]
            wiki_links.extend(wiki_matches)
            markdown_links.extend(md_matches)

        self.links.extend(wiki_links)
        self.links.extend(markdown_links)

        logger.debug("Extracted %d wiki links and %d markdown links",
                    len(wiki_links), len(markdown_links))

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

        self.last_update_date = final_date.strftime("%Y-%m-%d")

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


class ReadState:
    """Manages state machine for header/body parsing."""

    def __init__(self) -> None:
        self.is_reading_header = False
        self.is_reading_body = False
        self.divider_count = 0

    def handle_divider(self) -> None:
        """Updates state based on divider encounter."""
        self.divider_count += 1

        if self.divider_count == 1:
            self.is_reading_header = True
        elif self.divider_count == Zettel.COUNT_HEADER_DIVIDERS:
            self.is_reading_header = False
            self.is_reading_body = True
        else:
            self.is_reading_body = False

    def _validate_header(self) -> None:
        """Validates header termination."""
        if self.divider_count < Zettel.COUNT_HEADER_DIVIDERS:
            logger.error("Unclosed YAML header (found only %d dividers)", self.divider_count)
            msg = "Unclosed YAML header"
            raise ZettelFormatError(msg)
