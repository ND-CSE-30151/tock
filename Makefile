PYTHON=python3
SOURCE_DATE_EPOCH=$(shell git log -1 --format=%ct)

.PHONY: docs

test:
	$(PYTHON) -m unittest discover tests

docs:
	sphinx-build -M html docs/source "$@"

typecheck:
	mypy tock

upload:
	$(PYTHON) setup.py sdist
	twine upload dist/*
