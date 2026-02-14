# Contributing Guide

Thank you for your interest in contributing to this project!

## Development Setup

1. Fork the repository
2. Clone your fork:
   ```bash
   git clone https://github.com/yourusername/cursor_GCP_BigTable_NoSql_DE.git
   cd cursor_GCP_BigTable_NoSql_DE
   ```

3. Create a virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

4. Install dependencies:
   ```bash
   pip install -r pipelines/requirements.txt
   pip install -r requirements-dev.txt  # If exists
   ```

5. Install pre-commit hooks (optional):
   ```bash
   pip install pre-commit
   pre-commit install
   ```

## Code Style

- Follow PEP 8 for Python code
- Use Black for code formatting
- Maximum line length: 100 characters
- Use type hints where applicable

## Testing

- Write unit tests for new features
- Run tests before committing:
  ```bash
  pytest tests/unit/ -v
  ```
- Ensure test coverage doesn't decrease

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Write/update tests
4. Ensure all tests pass
5. Update documentation if needed
6. Submit a pull request
7. Wait for code review

## Commit Messages

Use clear, descriptive commit messages:
- Use present tense ("Add feature" not "Added feature")
- Start with a capital letter
- Keep the first line under 50 characters
- Add more details in the body if needed

## Terraform Changes

- Run `terraform fmt` before committing
- Run `terraform validate` to check syntax
- Test in dev environment first
- Update documentation for new resources

## Questions?

Open an issue or contact the maintainers.
