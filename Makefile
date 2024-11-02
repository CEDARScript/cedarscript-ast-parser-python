.PHONY: all version v test t dist d clean c

all: test version

version v:
	git describe --tags
	python -m setuptools_scm

test t:
	pytest --cov=src/cedarscript_ast_parser tests/ --cov-report term-missing

dist d: test
	scripts/check-version.sh
	rm -rf dist/cedarscript_*.whl dist/cedarscript_*.tar.gz
	python -m build && twine upload dist/*

clean c:
	rm -rfv out dist/cedarscript_*.whl dist/cedarscript_*.tar.gz build/bdist.* build/lib/cedarscript*
