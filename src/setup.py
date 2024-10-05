from setuptools import setup, find_packages
setup(
    name="cedarscript_ast_parser",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # Add any dependencies here
    ],
    author="Elifarley",
    author_email="elifarley@example.com",
    description="A library for CEDARScript AST parsing",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/CEDARScript/cedarscript-ast-parser",
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.12',
)