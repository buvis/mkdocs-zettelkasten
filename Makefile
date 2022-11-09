.PHONY: install test build check publish

install:
	pipenv install --dev

test:
	pipenv run mkdocs serve --livereload

build:
	rm -rf dist/*
	pipenv run python3 -m build

check:
	pipenv run twine check dist/*

publish:
	pipenv run python3 -m twine upload dist/*
