from __future__ import annotations

import datetime
import html
import re
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, TypedDict
from zoneinfo import ZoneInfo

if TYPE_CHECKING:
    from pathlib import Path

import logging

import yaml
from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.config import ZettelkastenConfig
from mkdocs_zettelkasten.plugin.constants import MOC_ROLES
from mkdocs_zettelkasten.plugin.utils.date_utils import convert_string_to_date
from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter
from mkdocs_zettelkasten.plugin.utils.git_utils import GitUtil
from mkdocs_zettelkasten.plugin.utils.patterns import MD_LINK, WIKI_LINK
from mkdocs_zettelkasten.plugin.utils.snippet_utils import truncate_around

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


class LinkRef(TypedDict):
    url: str
    title: str
    snippet: str | None


class SuggestionRef(TypedDict):
    url: str
    title: str
    reason: str
    confidence: str


class SequenceRef(TypedDict):
    url: str
    title: str


class SequenceTreeNode(TypedDict):
    url: str
    title: str
    current: bool
    children: list[SequenceTreeNode]


@dataclass(frozen=True)
class ZettelMeta:
    id: int
    title: str
    path: Path
    rel_path: str
    body: str
    last_update_date: str
    meta: dict
    links: list[str]
    link_snippets: dict[str, str]
    note_type: str | None = None
    maturity: str | None = None
    source: str | None = None
    role: str | None = None
    sequence_parent_id: int | None = None
    _id_key: str = "id"
    _date_key: str = "date"
    _last_update_key: str = "last_update"
    _type_key: str = "type"
    _maturity_key: str = "maturity"
    _role_key: str = "role"
    _sequence_key: str = "sequence"
    _id_format: str = r"^\d{14}$"
    _tz: ZoneInfo = field(default_factory=lambda: ZoneInfo("UTC"))
    _date_format: str = "%Y-%m-%d"

    @property
    def is_moc(self) -> bool:
        return self.role in MOC_ROLES


@dataclass
class ZettelRelationships:
    backlinks: list[LinkRef] = field(default_factory=list)
    moc_parents: list[LinkRef] = field(default_factory=list)
    unlinked_mentions: list[LinkRef] = field(default_factory=list)
    suggested_links: list[SuggestionRef] = field(default_factory=list)
    sequence_parent: SequenceRef | None = None
    sequence_children: list[SequenceRef] = field(default_factory=list)
    sequence_breadcrumb: list[SequenceRef] = field(default_factory=list)
    sequence_tree: list[SequenceTreeNode] = field(default_factory=list)


class ZettelFormatError(ValueError):
    """Exception raised for invalid zettel file format"""


class Zettel:
    def __init__(
        self,
        abs_src_path: Path,
        src_path: str,
        zettel_config: ZettelkastenConfig | None = None,
    ) -> None:
        cfg = zettel_config or ZettelkastenConfig()
        self._meta = self._build_meta(abs_src_path, src_path, cfg)
        self._rels = ZettelRelationships()

    @classmethod
    def from_parts(
        cls,
        meta: ZettelMeta,
        rels: ZettelRelationships | None = None,
    ) -> Zettel:
        instance = object.__new__(cls)
        instance._meta = meta  # noqa: SLF001
        instance._rels = rels or ZettelRelationships()  # noqa: SLF001
        return instance

    def __hash__(self) -> int:
        return hash(self._meta.id)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Zettel) and self._meta.id == other._meta.id

    # -- Meta properties (read-only) ----------------------------------------------

    @property
    def id(self) -> int:
        return self._meta.id

    @property
    def title(self) -> str:
        return self._meta.title

    @property
    def path(self) -> Path:
        return self._meta.path

    @property
    def rel_path(self) -> str:
        return self._meta.rel_path

    @property
    def body(self) -> str:
        return self._meta.body

    @property
    def last_update_date(self) -> str:
        return self._meta.last_update_date

    @property
    def meta(self) -> dict:
        return self._meta.meta

    @property
    def links(self) -> list[str]:
        return self._meta.links

    @property
    def link_snippets(self) -> dict[str, str]:
        return self._meta.link_snippets

    @property
    def note_type(self) -> str | None:
        return self._meta.note_type

    @property
    def maturity(self) -> str | None:
        return self._meta.maturity

    @property
    def source(self) -> str | None:
        return self._meta.source

    @property
    def role(self) -> str | None:
        return self._meta.role

    @property
    def sequence_parent_id(self) -> int | None:
        return self._meta.sequence_parent_id

    @property
    def is_moc(self) -> bool:
        return self._meta.is_moc

    # -- Relationship properties (read-write) --------------------------------------

    @property
    def backlinks(self) -> list[LinkRef]:
        return self._rels.backlinks

    @backlinks.setter
    def backlinks(self, value: list[LinkRef]) -> None:
        self._rels.backlinks = value

    @property
    def moc_parents(self) -> list[LinkRef]:
        return self._rels.moc_parents

    @moc_parents.setter
    def moc_parents(self, value: list[LinkRef]) -> None:
        self._rels.moc_parents = value

    @property
    def unlinked_mentions(self) -> list[LinkRef]:
        return self._rels.unlinked_mentions

    @unlinked_mentions.setter
    def unlinked_mentions(self, value: list[LinkRef]) -> None:
        self._rels.unlinked_mentions = value

    @property
    def suggested_links(self) -> list[SuggestionRef]:
        return self._rels.suggested_links

    @suggested_links.setter
    def suggested_links(self, value: list[SuggestionRef]) -> None:
        self._rels.suggested_links = value

    @property
    def sequence_parent(self) -> SequenceRef | None:
        return self._rels.sequence_parent

    @sequence_parent.setter
    def sequence_parent(self, value: SequenceRef | None) -> None:
        self._rels.sequence_parent = value

    @property
    def sequence_children(self) -> list[SequenceRef]:
        return self._rels.sequence_children

    @sequence_children.setter
    def sequence_children(self, value: list[SequenceRef]) -> None:
        self._rels.sequence_children = value

    @property
    def sequence_breadcrumb(self) -> list[SequenceRef]:
        return self._rels.sequence_breadcrumb

    @sequence_breadcrumb.setter
    def sequence_breadcrumb(self, value: list[SequenceRef]) -> None:
        self._rels.sequence_breadcrumb = value

    @property
    def sequence_tree(self) -> list[SequenceTreeNode]:
        return self._rels.sequence_tree

    @sequence_tree.setter
    def sequence_tree(self, value: list[SequenceTreeNode]) -> None:
        self._rels.sequence_tree = value

    # -- Parsing (static helpers) --------------------------------------------------

    @staticmethod
    def _build_meta(
        abs_src_path: Path,
        src_path: str,
        cfg: ZettelkastenConfig,
    ) -> ZettelMeta:
        try:
            content = abs_src_path.read_text(encoding="utf-8-sig", errors="strict")
        except OSError as err:
            logger.exception("Failed to read file %s", abs_src_path)
            msg = f"File {abs_src_path} read error"
            raise ZettelFormatError(msg) from err

        header_text, body_text, has_opening = parse_frontmatter(content)
        if not header_text:
            if has_opening:
                logger.error("Unclosed YAML header in file: %s", abs_src_path)
                msg = "Unclosed YAML header in file"
            else:
                logger.debug("Skipping non-zettel file: %s", abs_src_path)
                msg = "No frontmatter found"
            raise ZettelFormatError(msg)

        meta = Zettel._parse_yaml(header_text, abs_src_path)
        body_lines = body_text.splitlines()
        links, link_snippets = Zettel._extract_links(body_lines)
        alt_title = Zettel._find_alt_title(body_lines)

        zettel_id, title = Zettel._parse_core_metadata(
            meta, alt_title, abs_src_path, cfg
        )
        last_update_date = Zettel._determine_last_update_date(
            meta, zettel_id, abs_src_path, src_path, cfg
        )
        note_type, maturity, source, role, seq_parent = Zettel._parse_optional_metadata(
            meta, cfg
        )

        logger.debug(
            "Initialized zettel %s (ID: %s, Title: %s)",
            src_path,
            zettel_id,
            title,
        )

        return ZettelMeta(
            id=zettel_id,
            title=title,
            path=abs_src_path,
            rel_path=src_path,
            body=body_text,
            last_update_date=last_update_date,
            meta=meta,
            links=links,
            link_snippets=link_snippets,
            note_type=note_type,
            maturity=maturity,
            source=source,
            role=role,
            sequence_parent_id=seq_parent,
            _id_key=cfg.id_key,
            _date_key=cfg.date_key,
            _last_update_key=cfg.last_update_key,
            _type_key=cfg.type_key,
            _maturity_key=cfg.maturity_key,
            _role_key=cfg.role_key,
            _sequence_key=cfg.sequence_key,
            _id_format=cfg.id_format,
            _tz=cfg.timezone,
            _date_format=cfg.date_format,
        )

    @staticmethod
    def _parse_yaml(header: str, path: Path) -> dict:
        try:
            meta = yaml.safe_load(header) or {}

            if not isinstance(meta, dict):
                logger.error("Invalid YAML structure in %s: not a dictionary", path)
                msg = "Invalid YAML structure"
                raise ZettelFormatError(msg)

            logger.debug("Found metadata keys: %s", list(meta.keys()))

        except (ScannerError, AttributeError) as err:
            logger.exception("Failed to parse YAML in %s", path)
            msg = f"Invalid YAML in {path}"
            raise ZettelFormatError(msg) from err
        else:
            return meta

    @staticmethod
    def _find_alt_title(body: list[str]) -> str:
        for line in body:
            if line.lstrip().startswith("# "):
                return line.strip()[2:]
        return ""

    @staticmethod
    def _extract_links(body: list[str]) -> tuple[list[str], dict[str, str]]:
        links: list[str] = []
        link_snippets: dict[str, str] = {}
        wiki_count = 0
        md_count = 0

        for paragraph in Zettel._split_paragraphs(body):
            for m in WIKI_LINK.finditer(paragraph):
                url = m.group("url")
                links.append(url)
                wiki_count += 1
                if url not in link_snippets:
                    link_snippets[url] = Zettel._make_snippet(paragraph, m)

            for m in MD_LINK.finditer(paragraph):
                url = m.group("url")
                links.append(url)
                md_count += 1
                if url not in link_snippets:
                    link_snippets[url] = Zettel._make_snippet(paragraph, m)

        logger.debug(
            "Extracted %d wiki links and %d markdown links",
            wiki_count,
            md_count,
        )
        return links, link_snippets

    @staticmethod
    def _split_paragraphs(body: list[str]) -> list[str]:
        """Split body lines into paragraph strings, joined by spaces.

        Space-joining collapses lines for snippet/link-context matching.
        See also: UnlinkedMentionService._split_paragraphs (newline-joined,
        preserves structure for regex search).
        """
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
        link_text = match.group("title") or match.group("url")

        def _strip_links(text: str) -> str:
            text = WIKI_LINK.sub(lambda m: m.group("title") or m.group("url"), text)
            return MD_LINK.sub(lambda m: m.group("title"), text)

        prefix = html.escape(_strip_links(paragraph[: match.start()]))
        escaped_link = html.escape(link_text)
        suffix = html.escape(_strip_links(paragraph[match.end() :]))
        marked = f"<mark>{escaped_link}</mark>"
        clean = prefix + marked + suffix
        return truncate_around(clean, len(prefix), len(marked))

    @staticmethod
    def _parse_core_metadata(
        meta: dict,
        alt_title: str,
        path: Path,
        cfg: ZettelkastenConfig,
    ) -> tuple[int, str]:
        raw_id = meta.get(cfg.id_key)
        if not raw_id:
            logger.error("Missing required ID in zettel: %s", path)
            msg = "Missing zettel ID"
            raise ZettelFormatError(msg)

        try:
            zettel_id = int(raw_id)
        except (ValueError, TypeError) as err:
            logger.error("ID %r is not a valid integer in %s", raw_id, path)
            msg = f"ID {raw_id!r} is not a valid integer"
            raise ZettelFormatError(msg) from err

        if not re.fullmatch(cfg.id_format, str(raw_id)):
            logger.error(
                "ID %r does not match format %s in %s",
                raw_id,
                cfg.id_format,
                path,
            )
            msg = f"ID {raw_id!r} does not match format {cfg.id_format}"
            raise ZettelFormatError(msg)

        if meta.get("title"):
            title = meta["title"]
        elif alt_title:
            title = alt_title
        else:
            title = Zettel._generate_filename_title(path, cfg.id_format)

        return zettel_id, title

    @staticmethod
    def _parse_optional_metadata(
        meta: dict,
        cfg: ZettelkastenConfig,
    ) -> tuple[str | None, str | None, str | None, str | None, int | None]:
        raw_type = meta.get(cfg.type_key)
        note_type = str(raw_type) if raw_type is not None else None
        raw_maturity = meta.get(cfg.maturity_key)
        maturity = str(raw_maturity) if raw_maturity is not None else None
        raw_source = meta.get("source")
        source = str(raw_source) if raw_source is not None else None
        raw_role = meta.get(cfg.role_key)
        role = str(raw_role) if raw_role is not None else None
        raw_seq = meta.get(cfg.sequence_key)
        seq_parent = int(raw_seq) if raw_seq is not None else None
        return note_type, maturity, source, role, seq_parent

    @staticmethod
    def _generate_filename_title(path: Path, id_format: str) -> str:
        stem = path.stem
        id_prefix = id_format.lstrip("^").rstrip("$")
        clean_stem = re.sub(id_prefix, "", stem)
        return clean_stem.replace("_", " ").replace("-", " ").strip().capitalize()

    @staticmethod
    def _determine_last_update_date(
        meta: dict,
        zettel_id: int,
        path: Path,
        rel_path: str,
        cfg: ZettelkastenConfig,
    ) -> str:
        candidate_date = Zettel._get_initial_candidate_date(meta, zettel_id, cfg)
        revision_date = Zettel._get_revision_date(path, cfg.timezone)

        if cfg.last_update_key in meta:
            final_date = candidate_date
        else:
            final_date = max(candidate_date, revision_date, key=lambda d: d.timestamp())
            logger.debug(
                "Using later date between metadata (%s) and modification (%s) for %s",
                candidate_date.strftime("%Y-%m-%d"),
                revision_date.strftime("%Y-%m-%d"),
                rel_path,
            )

        return final_date.strftime(cfg.date_format)

    @staticmethod
    def _get_initial_candidate_date(
        meta: dict,
        zettel_id: int,
        cfg: ZettelkastenConfig,
    ) -> datetime.datetime:
        for key in [cfg.last_update_key, cfg.date_key]:
            if date := convert_string_to_date(meta.get(key, ""), tz=cfg.timezone):
                return date

        id_date = convert_string_to_date(str(zettel_id), tz=cfg.timezone)
        if id_date:
            return id_date

        return datetime.datetime.now(tz=cfg.timezone)

    @staticmethod
    def _get_revision_date(path: Path, tz: ZoneInfo) -> datetime.datetime:
        if GitUtil.is_tracked(str(path)):
            git_date = GitUtil.get_revision_date_for_file(str(path))
            if git_date is not None:
                return git_date

        return Zettel._get_mtime(path, tz)

    @staticmethod
    def _get_mtime(path: Path, tz: ZoneInfo) -> datetime.datetime:
        st_mtime = path.stat().st_mtime
        return datetime.datetime.fromtimestamp(st_mtime, tz=tz)
