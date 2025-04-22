from pathlib import Path
import jinja2


def create_jinja_environment(template_path: Path = None) -> jinja2.Environment:
    """
    Create a Jinja2 environment for template rendering.
    """
    if template_path:
        return jinja2.Environment(
            loader=jinja2.FileSystemLoader(str(template_path.parent))
        )
    # Fallback to default templates directory
    import os

    default_template_path = Path(os.path.dirname(__file__)).parent / "templates"
    return jinja2.Environment(
        loader=jinja2.FileSystemLoader(str(default_template_path))
    )
