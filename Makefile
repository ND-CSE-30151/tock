PYTHON=python3

.PHONY: docs

test:
	$(PYTHON) -m unittest discover tests

docs:
	sphinx-build -M html docs/source "$@"

typecheck:
	mypy tock
