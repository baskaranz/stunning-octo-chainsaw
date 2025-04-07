# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Build & Run Commands
```bash
# Install dependencies
pip install -e .

# Run service
python main.py

# Run linting
flake8 app/ tests/

# Run type checking
mypy app/ tests/

# Run all tests
pytest tests/

# Run a specific test file
pytest tests/path/to/test_file.py

# Run a specific test case
pytest tests/path/to/test_file.py::TestClass::test_method
```

## Code Style Guidelines
- **Imports**: Group imports: standard library, third-party, local. Sort alphabetically.
- **Formatting**: Follow PEP 8. Line length max 100 characters.
- **Types**: Use type hints for all function parameters and return values.
- **Naming**: 
  - snake_case for variables, functions, methods
  - PascalCase for classes
  - UPPER_CASE for constants
- **Error Handling**: Use custom exceptions from common.errors. Log errors appropriately.
- **Testing**: Write tests for all new functionality. Use pytest fixtures from conftest.py.
- **Documentation**: Document all public APIs with docstrings.