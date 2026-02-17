from pathlib import Path

import jinja2

from mkdocs_zettelkasten.plugin.utils.jinja_utils import create_jinja_environment


def test_default_template_path() -> None:
    env = create_jinja_environment()
    assert isinstance(env, jinja2.Environment)
    assert isinstance(env.loader, jinja2.FileSystemLoader)
    template = env.get_template("tags.md.j2")
    assert template is not None


def test_custom_template_path(tmp_path: Path) -> None:
    tmpl = tmp_path / "custom.html.j2"
    tmpl.write_text("{{ content }}")

    env = create_jinja_environment(tmpl)
    assert isinstance(env.loader, jinja2.FileSystemLoader)
    template = env.get_template("custom.html.j2")
    assert template is not None
