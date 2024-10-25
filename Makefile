.PHONY: all version test dist clean

all: test version

version:
	python -m setuptools_scm

test:
	pytest --cov=src/cedarscript_ast_parser tests/ --cov-report term-missing

dist: test
	scripts/check-version.sh
	rm -rf dist/
	python -m build && twine upload dist/*

clean:
	rm -f /dist/
