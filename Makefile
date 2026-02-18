.PHONY: install update test test-e2e run clean

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

clean:
	rm -rf .venv
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
