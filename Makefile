.PHONY: all version test dist clean

all: test version

version:
	git describe --tags
	python -m setuptools_scm

test:
	pytest --cov=src/cedarscript_ast_parser tests/ --cov-report term-missing

dist: test
	scripts/check-version.sh
	rm -rf dist/cedarscript_*.whl dist/cedarscript_*.tar.gz
	python -m build && twine upload dist/*

clean:
	rm -rfv out dist/cedarscript_*.whl dist/cedarscript_*.tar.gz build/bdist.* build/lib/cedarscript*
