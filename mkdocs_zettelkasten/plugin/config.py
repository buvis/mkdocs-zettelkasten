from __future__ import annotations

from dataclasses import dataclass, field
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ZettelkastenConfig:
    log_level: str = "INFO"
    log_format: str = "%(log_color)s%(levelname)-7s%(reset)s -  [%(green)s%(asctime)s.%(msecs)03d%(reset)s] <%(blue)s%(name)s%(reset)s>: %(message_log_color)s%(message)s%(reset)s"
    id_key: str = "id"
    date_key: str = "date"
    last_update_key: str = "last_update"
    tags_key: str = "tags"
    type_key: str = "type"
    maturity_key: str = "maturity"
    role_key: str = "role"
    sequence_key: str = "sequence"
    id_format: str = r"^\d{14}$"
    timezone: ZoneInfo = field(default_factory=lambda: ZoneInfo("UTC"))
    date_format: str = "%Y-%m-%d"
    validation_enabled: bool = True
    editor_enabled: bool = False
    editor_repo: str = ""
    editor_branch: str = "master"
    editor_docs_prefix: str = "docs"
    icon_references: str = "fa fa-book"
    icon_backlinks: str = "fa fa-link"
    file_suffix: str = ".md"
    graph_enabled: bool = False
    preview_enabled: bool = False
    suggestions_enabled: bool = False
    workflow_enabled: bool = False
    transclusion_strip_heading: bool = True
    minify_js: bool = True
