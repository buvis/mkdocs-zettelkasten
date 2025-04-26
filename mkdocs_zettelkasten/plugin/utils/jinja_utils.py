from __future__ import annotations

from pathlib import Path

import jinja2


def create_jinja_environment(template_path: Path | None = None) -> jinja2.Environment:
    """
    Create a Jinja2 environment for template rendering.
    """
    if template_path:
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent)),
            autoescape=True,
        )
    # Fallback to default templates directory
    default_template_path = Path(__file__).parent.parent / "templates"

    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(default_template_path)),
        autoescape=True,
    )
