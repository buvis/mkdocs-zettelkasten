from __future__ import annotations

import logging
from pathlib import Path

import jinja2

logger = logging.getLogger(
    __name__.replace("mkdocs_zettelkasten.plugin.", "mkdocs.plugins.zettelkasten.")
)


def create_jinja_environment(template_path: Path | None = None) -> jinja2.Environment:
    """
    Create a Jinja2 environment for template rendering.
    """
    if template_path:
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent)),
            autoescape=True,
        )
    default_template_path = Path(__file__).parent.parent / "templates"
    logger.debug(
        "Falling back to default templates directory: %s",
        default_template_path,
    )

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(default_template_path)),
        autoescape=True,
    )
