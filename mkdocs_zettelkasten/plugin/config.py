from __future__ import annotations

from dataclasses import dataclass
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ZettelkastenConfig:
    log_level: str
    log_format: str
    id_key: str
    date_key: str
    last_update_key: str
    tags_key: str
    type_key: str
    maturity_key: str
    role_key: str
    sequence_key: str
    id_format: str
    timezone: ZoneInfo
    date_format: str
    validation_enabled: bool
    editor_enabled: bool
    editor_repo: str
    editor_branch: str
    editor_docs_prefix: str
    icon_references: str
    icon_backlinks: str
    file_suffix: str
    graph_enabled: bool
    preview_enabled: bool
    suggestions_enabled: bool
    workflow_enabled: bool
    transclusion_strip_heading: bool
    minify_js: bool
