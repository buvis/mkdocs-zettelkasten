.PHONY: install update test test-e2e run run-selenized run-editor run-no-validation clean

install:
	uv sync

update:
	uv lock --upgrade
	uv sync

test:
	uv run pytest tests/plugin/

test-e2e:
	uv run pytest tests/e2e/ -v

run:
	uv run mkdocs serve --livereload

run-selenized:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-selenized.yml

run-editor:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-editor.yml

run-no-validation:
	uv run mkdocs serve --livereload -f tests/e2e/configs/mkdocs-no-validation.yml

clean:
	rm -rf .venv
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
