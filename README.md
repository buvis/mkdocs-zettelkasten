# MkDocs Zettelkasten

This is a [Zettelkasten](https://zettelkasten.de) theme and plugin for [MkDocs](https://www.mkdocs.org). It renders the MkDocs pages as cards (zettels).

For more information, head on over to [the documentation](https://buvis.github.io/mkdocs-zettelkasten/)

## Install

```bash
pip install mkdocs-zettelkasten
```

## Development

```bash
uv sync                    # install deps
uv run playwright install  # install browsers (first time only)
```

### Run locally

```bash
make run                # default (solarized, validation on)
make run-selenized      # selenized theme
make run-editor         # markdown editor enabled
make run-no-validation  # validation disabled
```

### Tests

```bash
make test      # unit tests (~0.3s)
make test-e2e  # playwright e2e tests (~27s)
```

Manual test checklists for visual/interactive features live in `.local/testscripts/`.

## Release

`mise` adds `dev/bin` to PATH. Tags with `rc` in the name publish to TestPyPI; stable tags go to PyPI. Manual workflow dispatch defaults to TestPyPI.

```bash
release patch|minor|major              # tag and push -> CI publishes to PyPI
release --pre rc1                      # pre-release current version to TestPyPI
release --pre rc1 minor                # bump + pre-release to TestPyPI
release                                # after rc: strip suffix, release stable to PyPI
release --dry-run patch                # preview without doing anything
```

**First-time setup** (already done for mkdocs-zettelkasten):
- pypi.org: add trusted publisher (owner: `buvis`, repo: `mkdocs-zettelkasten`, workflow: `publish.yml`, env: `pypi`)
- test.pypi.org: same, env: `testpypi`
- GitHub repo settings: create `pypi` and `testpypi` environments

The release script updates the pinned version in `.github/workflows/requirements.txt` (used by docs deployment), commits, tags, and pushes both. Version derives from git tags via hatch-vcs — no version field in `pyproject.toml`. This works for pure Python packages. Projects with native extensions (like buvis/gems with maturin/Rust) need an explicit version in `pyproject.toml` because maturin reads it at build time.
