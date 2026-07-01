PYTHON ?= python3
CONFIG ?= config.txt
 
.PHONY: install build run debug clean lint lint-strict
 
install:
	@if [ -n "$$VIRTUAL_ENV" ]; then \
		$(PYTHON) -m pip install -r requirements.txt; \
	else \
		$(PYTHON) -m pip install --user -r requirements.txt || $(PYTHON) -m pip install -r requirements.txt; \
	fi

build: clean
	$(PYTHON) -m build
	cp dist/mazegen-*.whl .
 
run:
	$(PYTHON) a_maze_ing.py $(CONFIG)
 
debug:
	$(PYTHON) -m pdb a_maze_ing.py $(CONFIG)
 
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	rm -rf .mypy_cache
	rm -rf build dist *.egg-info src/mazegen.egg-info
	rm -f mazegen-*.whl mazegen-*.tar.gz
 
lint:
	flake8 .
	MYPYPATH=. mypy . --warn-return-any --warn-unused-ignores \
		--ignore-missing-imports --disallow-untyped-defs \
		--check-untyped-defs
 
lint-strict:
	flake8 .
	MYPYPATH=. mypy . --strict
