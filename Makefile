.PHONY: install update test run clean

install:
	uv sync

update:
	uv lock --upgrade
	uv sync

test:
	uv run pytest

run:
	uv run mkdocs serve --livereload

clean:
	rm -rf .venv
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
