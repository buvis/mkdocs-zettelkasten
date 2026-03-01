.PHONY: install update test test-e2e lint typecheck check run run-selenized run-editor run-no-validation run-graph run-preview run-math clean

install:
	uv sync

update:
	uv lock --upgrade
	uv sync

test:
	uv run pytest tests/plugin/

test-e2e:
	uv run pytest tests/e2e/ -v

lint:
	uv run ruff check . && uv run ruff format --check .

typecheck:
	uv run pyright mkdocs_zettelkasten/

check: lint typecheck test

run:
	uv run mkdocs serve --livereload

run-selenized:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-selenized.yml

run-editor:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-editor.yml

run-no-validation:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-no-validation.yml

run-graph:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-graph.yml

run-preview:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-preview.yml

run-math:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-math.yml

clean:
	rm -rf .venv
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
