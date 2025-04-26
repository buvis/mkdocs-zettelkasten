from __future__ import annotations

import datetime
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path
from zoneinfo import ZoneInfo

import tzlocal
import yaml
from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date
from mkdocs_zettelkasten.plugin.utils.git_utils import GitUtil
from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK

local_tz = ZoneInfo(tzlocal.get_localzone_name())


class ZettelFormatError(ValueError):
    """Exception raised for invalid zettel file format"""


class Zettel:
    COUNT_HEADER_DIVIDERS = 2
    MARK_DIVIDER = "---"

    def __init__(self, abs_src_path: Path) -> None:
        self.id: int = 0
        self.title: str = ""
        self.path: Path = abs_src_path
        self.backlinks: list[dict[str, str]] = []
        self.links: list[str] = []
        self.last_update_date: str = ""

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
            msg = f"File {self.path} read error"
            raise ZettelFormatError(msg) from err

        self._validate_header(read_state)
        return header, body

    def _validate_header(self, read_state: ReadState) -> None:
        """Validate header termination."""
        if read_state.divider_count < Zettel.COUNT_HEADER_DIVIDERS:
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
                msg = "Invalid YAML structure"
                raise ZettelFormatError(msg)

        except (ScannerError, AttributeError) as err:
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
        for line in body:
            self.links.extend(m.groupdict()["url"] for m in WIKI_LINK.finditer(line))
            self.links.extend(m.groupdict()["url"] for m in MD_LINK.finditer(line))

    def _set_core_metadata(self, meta: dict, alt_title: str) -> None:
        """Sets fundamental metadata fields."""
        if not meta.get("id"):
            msg = "Missing zettel ID"
            raise ZettelFormatError(msg)

        self.id = meta["id"]
        self.title = meta.get("title") or alt_title or self._generate_filename_title()
        self._determine_last_update_date(meta)

    def _generate_filename_title(self) -> str:
        """Generates title from filename using pattern matching."""
        stem = self.path.stem
        clean_stem = re.sub(r"^\d{14}", "", stem)
        return clean_stem.replace("_", " ").replace("-", " ").strip().capitalize()

    def _determine_last_update_date(self, meta: dict) -> None:
        """Determines most recent valid date from multiple sources."""
        candidate_date = self._get_initial_candidate_date(meta)
        revision_date = self._get_revision_date()

        if "last_update" in meta:
            final_date = candidate_date
        else:
            final_date = max(candidate_date, revision_date, key=lambda d: d.timestamp())
        self.last_update_date = final_date.strftime("%Y-%m-%d")

    def _get_initial_candidate_date(self, meta: dict) -> datetime.datetime:
        """Gets first valid date from metadata sources."""
        for field in ["last_update", "date"]:
            if date := convert_string_to_date(meta.get(field, "")):
                return date
        return convert_string_to_date(str(self.id)) or datetime.datetime.now(
            tz=local_tz,
        )

    def _get_revision_date(self) -> datetime.datetime:
        """Gets revision date from VCS or filesystem."""
        if self._is_version_controlled():
            return GitUtil().get_revision_date_for_file(str(self.path))

        st_mtime = self.path.stat().st_mtime
        if isinstance(st_mtime, (int, float)):
            return datetime.datetime.fromtimestamp(st_mtime, tz=local_tz)

        if isinstance(st_mtime, datetime.datetime):
            if st_mtime.tzinfo is None:
                st_mtime = st_mtime.replace(tzinfo=local_tz)
            return st_mtime

        msg = f"Unexpected type for st_mtime: {type(st_mtime)}"
        raise TypeError(msg)

    def _is_version_controlled(self) -> bool:
        """Checks if file is under version control."""
        return any(host in str(self.path) for host in ["//github.com", "//gitlab.com"])


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
            msg = "Unclosed YAML header"
            raise ZettelFormatError(msg)
