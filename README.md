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

### Testing

Three levels of testing, from fast to thorough:

**1. Unit tests** — plugin logic without building the site:

```bash
make test      # ~0.3s, 124 tests
```

**2. E2E tests** — playwright builds the site from `docs/`, serves it, and checks the UI automatically:

```bash
make test-e2e  # ~27s, 63 tests
```

**3. Manual acceptance** — build and serve the site from `docs/`, open localhost:8000 in a browser and walk through the checklists in `.local/testscripts/`:

```bash
make run                # default (solarized, validation on)
make run-selenized      # selenized color scheme
make run-editor         # markdown editor enabled
make run-no-validation  # validation disabled
```

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

Stable releases (no `rc` in tag) auto-create a GitHub Release with a changelog generated from conventional commits since the previous tag.
