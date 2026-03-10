from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from mkdocs_zettelkasten.plugin.utils.frontmatter import parse_frontmatter

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def extract_file_metadata(filename: str, docs_dir: str) -> dict[str, Any]:
    """Extract YAML metadata from a Markdown file."""
    file_path = Path(docs_dir) / filename
    logger.debug("Extracting metadata from file: %s.", file_path)
    try:
        content = file_path.read_text(encoding="utf-8-sig")
        header_text, _, has_opening = parse_frontmatter(content)
        if not header_text:
            if has_opening:
                logger.warning("Unclosed YAML frontmatter in file: %s.", file_path)
            else:
                logger.debug("No YAML frontmatter in file: %s.", file_path)
            return {}
        metadata = yaml.safe_load(header_text)
        if not isinstance(metadata, dict):
            return {}
    except (OSError, UnicodeDecodeError, yaml.YAMLError) as e:
        logger.warning("Failed to read metadata from %s: %s", file_path, e)
        return {}
    else:
        logger.debug("Metadata extracted successfully from file: %s.", file_path)
        return metadata
