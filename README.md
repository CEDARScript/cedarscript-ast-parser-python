# CEDARScript Parser

CEDARScript Parser is a Python library for parsing and interpreting CEDARScript, a SQL-like language designed for concise code analysis, manipulation, and refactoring tasks.

## What is CEDARScript?

CEDARScript (Concise Examination, Development, And Refactoring Script) is a domain-specific language that aims to improve how AI coding assistants interact with codebases and communicate their code modification intentions. It provides a standardized way to express complex code modification and analysis operations, making it easier for AI-assisted development tools to understand and execute these tasks.

## Features

- Parse CEDARScript code into an Abstract Syntax Tree (AST)
- Support for various code manipulation commands (create, delete, move, update)
- SQL-like syntax for intuitive code querying and manipulation
- High-level abstractions for complex refactoring operations
- Language-agnostic design for versatile code analysis
- Reduced token usage via semantic-level code transformations
- Scalable to larger codebases with minimal token usage
- Error handling and reporting for invalid scripts
- Return results in XML format for easier parsing and processing by LLM systems

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
