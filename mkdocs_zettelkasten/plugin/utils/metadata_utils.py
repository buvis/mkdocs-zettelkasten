from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, TextIO

from yaml.scanner import ScannerError

from mkdocs_zettelkasten.plugin.entities.zettel import Zettel

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def extract_file_metadata(filename: str, docs_dir: str) -> dict[str, Any]:
    """
    Extract YAML metadata from a Markdown file.
    """
    file_path = Path(docs_dir) / filename
    logger.debug("Extracting metadata from file: %s.", file_path)
    try:
        with file_path.open(encoding="utf-8") as f:
            metadata = _read_yaml_frontmatter(f)
            if metadata is None:
                logger.warning(
                    "No YAML frontmatter found or failed to parse in file: %s.",
                    file_path,
                )
                return {}
            logger.debug("Metadata extracted successfully from file: %s.", file_path)
            return metadata
    except FileNotFoundError:
        logger.exception("File not found: %s.", file_path)
        return {}
    except Exception:
        logger.exception("Unexpected error while reading file %s.", file_path)
        return {}


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
            metadata = yaml.safe_load("".join(yaml_lines))
            logger.debug("YAML frontmatter parsed successfully.")
        except ScannerError:
            logger.warning("Failed to parse YAML frontmatter due to ScannerError.")
            return None
        else:
            return metadata

    return None
