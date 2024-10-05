from setuptools import setup, find_packages

setup(
    name='cedarscript_ast_parser',
    version='0.1.0',
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    package_data={
        'cedarscript_ast_parser': ['../vendor/libtree-sitter-cedar.*'],
    },
    include_package_data=True,
    install_requires=[
        'tree-sitter>=0.20.1',
    ],
)
