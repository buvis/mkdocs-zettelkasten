.PHONY: install update run

install:
	poetry install

update:
	poetry updated

run:
	poetry run mkdocs serve --livereload
