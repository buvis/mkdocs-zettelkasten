.PHONY: install update test run clean

install:
	poetry lock
	poetry install

update:
	poetry updated

test:
	poetry run pytest

run:
	poetry run mkdocs serve --livereload

clean:
	poetry env remove --all
	find . -name '*.pyc' -delete
	find . -type d -name '__pycache__' -exec rm -r {} +
