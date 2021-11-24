.PHONY: install test publish

install:
	pipenv install --dev

test:
	pipenv run mkdocs serve --livereload

publish:
	rm -rf dist/*
	python3 -m build
	python3 -m twine upload dist/*
