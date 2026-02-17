# MkDocs Zettelkasten

This is a [Zettelkasten](https://zettelkasten.de) theme and plugin for [MkDocs](https://www.mkdocs.org). It renders the MkDocs pages as cards (zettels).

For more information, head on over to [the documentation](https://buvis.github.io/mkdocs-zettelkasten/)

## Install

```bash
pip install mkdocs-zettelkasten
```

## Development

```bash
uv sync
uv run pytest
uv run mkdocs serve --livereload
```

## Release

```bash
release patch|minor|major              # tag and push -> CI publishes to PyPI
release --pre rc1                      # pre-release current version to TestPyPI
release --pre rc1 minor                # bump + pre-release to TestPyPI
release                                # after rc: strip suffix, release stable to PyPI
release --dry-run patch                # preview without doing anything
```

Version derives from git tags via hatch-vcs — no version field in `pyproject.toml`, no bump commits. The release script only creates and pushes a tag. This works for pure Python packages. Projects with native extensions (like buvis/gems with maturin/Rust) need an explicit version in `pyproject.toml` because maturin reads it at build time.
