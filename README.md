# CEDARScript AST Parser

[![PyPI version](https://badge.fury.io/py/cedarscript-ast-parser.svg)](https://pypi.org/project/cedarscript-ast-parser/)
[![Python Versions](https://img.shields.io/pypi/pyversions/cedarscript-ast-parser.svg)](https://pypi.org/project/cedarscript-ast-parser/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

`CEDARScript AST Parser` is a Python library for parsing and interpreting `CEDARScript`, a SQL-like language designed for concise code analysis, manipulation, and refactoring tasks.

## What is CEDARScript?

[CEDARScript](https://bit.ly/cedarscript) (_Concise Examination, Development, And Refactoring Script_) is a domain-specific language that
aims to improve how AI coding assistants interact with codebases and communicate their code modification intentions.
It provides a standardized way to express complex code modification and analysis operations, making it easier for 
AI-assisted development tools to understand and execute these tasks.

## Features

- Parse `CEDARScript` Abstract Syntax Tree (`AST`) that was generated by Tree-Sitter into a list of commands
- Support for various code manipulation and analysis commands (CREATE, UPDATE, RM, MV, SELECT)
- Return results in `XML` format for easier parsing and processing by LLM systems

## Installation

You can install CEDARScript Parser using pip:

```
pip install cedarscript-ast-parser
```

## Usage

Here's a quick example of how to use CEDARScript Parser:

```python
from cedarscript_ast_parser import CEDARScriptASTParser

parser = CEDARScriptASTParser()
code = """
CREATE FILE "example.py"
UPDATE FILE "example.py"
    INSERT AT END OF FILE
        CONTENT
            print("Hello, World!")
        END CONTENT
END UPDATE
"""

commands, errors = parser.parse_script(code)

if errors:
    for error in errors:
        print(f"Error: {error}")
else:
    for command in commands:
        print(f"Parsed command: {command}")
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License.
