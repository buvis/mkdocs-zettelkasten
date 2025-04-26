from __future__ import annotations

from pathlib import Path
from typing import Any, TextIO

from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel


def extract_file_metadata(filename: str, docs_dir: str) -> dict[str, Any]:
    """
    Extract YAML metadata from a Markdown file.
    """
    file_path = Path(docs_dir) / filename
    with file_path.open(encoding="utf-8") as f:
        return _read_yaml_frontmatter(f) or {}


def _read_yaml_frontmatter(file_handler: TextIO) -> dict[str, Any] | None:
    """
    Read YAML frontmatter from a file handler.
    """
    import yaml

    yaml_lines = []
    delimiter_count = 0
    for line in file_handler:
        stripped = line.strip()
        if stripped == "---":
            delimiter_count += 1
            if delimiter_count == Zettel.COUNT_HEADER_DIVIDERS:
                break
            continue
        if delimiter_count == 1:
            yaml_lines.append(line)
    if yaml_lines:
        try:
            return yaml.safe_load("".join(yaml_lines))
        except ScannerError:
            return None
    return None
