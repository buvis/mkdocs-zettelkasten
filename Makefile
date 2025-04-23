.PHONY: install update test run

install:
	poetry install

update:
	poetry updated

test:
	poetry run pytest

run:
	poetry run mkdocs serve --livereload
