from setuptools import setup, find_packages

setup(
    name="cedarscript_ast_parser",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "tree-sitter>=0.20.1",
    ],
    package_data={
        "cedarscript_ast_parser": ["*.so", "*.dylib", "*.dll"],
    },
    author="Elifarley",
    author_email="elifarley@example.com",
    description="A library for CEDARScript AST parsing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/CEDARScript/cedarscript-ast-parser",
    classifiers=[
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: Text Processing :: Linguistic",
    ],
    python_requires='>=3.12',
)
