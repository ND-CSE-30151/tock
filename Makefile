PYTHON=python3

test:
	$(PYTHON) -m unittest discover tests

typecheck:
	mypy tock