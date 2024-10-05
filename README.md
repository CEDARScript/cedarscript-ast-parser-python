# CEDARScript Parser

CEDARScript Parser is a Python library for parsing and interpreting CEDARScript, a domain-specific language for code editing and refactoring tasks.

## Features

- Parse CEDARScript code into an Abstract Syntax Tree (AST)
- Support for various code manipulation commands (create, delete, move, update)
- Error handling and reporting for invalid scripts

## Installation

You can install CEDARScript Parser using pip:

```
pip install cedarscript-parser
```

## Usage

Here's a quick example of how to use CEDARScript Parser:

```python
from cedarscript_parser import CEDARScriptASTParser

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
