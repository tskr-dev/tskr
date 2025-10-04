# Contributing to Tskr

Thank you for your interest in contributing to Tskr! This document provides guidelines and information for contributors.

## 🚀 Quick Start

1. **Fork the repository** on GitHub
2. **Clone your fork** locally:

   ```bash
   git clone https://github.com/YOUR_USERNAME/tskr.git
   cd tskr
   ```

3. **Set up development environment**:

   ```bash
   # Install with development dependencies
   pip install -e ".[dev]"

   # Or using uv (recommended)
   uv sync
   ```

4. **Create a feature branch**:

   ```bash
   git checkout -b feature/your-feature-name
   ```

5. **Make your changes** and commit them
6. **Push to your fork** and create a Pull Request

## 🛠️ Development Setup

### Prerequisites

- Python 3.8 or higher
- Git
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Environment Setup

```bash
# Clone the repository
git clone https://github.com/tskr-dev/tskr.git
cd tskr

# Install dependencies (using uv - recommended)
uv sync

# Or using pip
pip install -e ".[dev]"

# Verify installation
tskr --help
```

### Development Dependencies

The project includes these development tools:

- **pytest**: Testing framework
- **ruff**: Fast Python linter
- **mypy**: Static type checking
- **pyinstaller**: Binary building

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/tskr --cov-report=html

# Run specific test file
pytest tests/test_models.py

# Run tests matching a pattern
pytest -k "test_task_creation"
```

### Writing Tests

- Place tests in the `tests/` directory
- Use descriptive test names: `test_should_create_task_with_priority`
- Follow the AAA pattern: Arrange, Act, Assert
- Use fixtures from `conftest.py` for common setup

Example test:

```python
def test_should_create_task_with_high_priority(test_project):
    """Test creating a task with high priority."""
    # Arrange
    service = TaskService(test_project.project_root)

    # Act
    task = service.create_task(
        title="Critical bug fix",
        priority=Priority.HIGH,
        actor="test-user"
    )

    # Assert
    assert task.priority == Priority.HIGH
    assert task.title == "Critical bug fix"
    assert task.status == Status.BACKLOG
```

## 🎨 Code Style

We use automated tools to maintain consistent code style:

### Linting

```bash
# Run linter
ruff check .

# Fix auto-fixable issues
ruff check --fix .
```

### Type Checking

```bash
# Run type checker
mypy src/
```

### Pre-commit Checks

Before committing, run:

```bash
# Format, lint, and type check
uv run ruff check . && mypy src/ && pytest
```

## 📁 Project Structure

```text
tskr/
├── src/tskr/              # Main package
│   ├── __init__.py        # Package initialization
│   ├── cli.py             # Main CLI application
│   ├── models.py          # Data models (Task, Project, etc.)
│   ├── services.py        # Business logic
│   ├── storage.py         # Data persistence layer
│   ├── formatters.py      # Output formatting
│   ├── utils.py           # Utility functions
│   ├── config.py          # Configuration management
│   ├── context.py         # Project context handling
│   ├── repository.py      # Git integration
│   └── commands/          # CLI command implementations
│       ├── add.py         # Add command
│       ├── ls.py          # List command
│       └── ...
├── tests/                 # Test suite
├── docs/                  # Documentation
├── pyproject.toml         # Project configuration
└── README.md              # Project documentation
```

## 🏗️ Architecture

### Core Components

1. **Models** (`models.py`): Pydantic models for data validation
2. **Services** (`services.py`): Business logic and orchestration
3. **Storage** (`storage.py`): File-based persistence (JSONL)
4. **CLI** (`cli.py`): Typer-based command interface
5. **Commands** (`commands/`): Individual command implementations

### Design Principles

- **Separation of Concerns**: Clear boundaries between CLI, business logic, and storage
- **Type Safety**: Comprehensive type hints and Pydantic validation
- **Testability**: Dependency injection and mockable interfaces
- **Git-Friendly**: Human-readable storage formats
- **LLM-Friendly**: Structured data and clear event logging

## 🐛 Bug Reports

When reporting bugs, please include:

1. **Tskr version**: `tskr version`
2. **Python version**: `python --version`
3. **Operating system**: Windows/macOS/Linux
4. **Steps to reproduce** the issue
5. **Expected behavior**
6. **Actual behavior**
7. **Error messages** (if any)

Use our [bug report template](.github/ISSUE_TEMPLATE/bug_report.md).

## 💡 Feature Requests

For feature requests:

1. **Check existing issues** to avoid duplicates
2. **Describe the problem** you're trying to solve
3. **Propose a solution** with examples
4. **Consider alternatives** you've evaluated
5. **Discuss implementation** if you have ideas

Use our [feature request template](.github/ISSUE_TEMPLATE/feature_request.md).

## 🔄 Pull Request Process

### Before You Start

1. **Check existing issues** - your idea might already be in progress
2. **Open an issue** for discussion (for significant changes)
3. **Fork the repository** and create a feature branch

### Pull Request Guidelines

1. **One feature per PR** - keep changes focused
2. **Write clear commit messages**:

   ```text
   feat: add task dependency tracking

   - Add depends_on field to Task model
   - Implement dependency validation in TaskService
   - Add CLI support for --depends-on flag

   Closes #123
   ```

3. **Update tests** for your changes
4. **Update documentation** if needed
5. **Ensure all checks pass**:
   - Tests pass
   - Linting passes (ruff)
   - Type checking passes (mypy)

### Commit Message Format

We follow conventional commits:

- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks

### Review Process

1. **Automated checks** must pass
2. **Code review** by maintainers
3. **Testing** on different platforms (if applicable)
4. **Merge** after approval

## 🏷️ Release Process

Releases are handled by maintainers:

1. **Version bump** in `src/tskr/__init__.py`
2. **Update CHANGELOG.md**
3. **Create GitHub release**
4. **Publish to PyPI** (automated via GitHub Actions)

## 📚 Documentation

### Types of Documentation

1. **README.md** - Project overview and quick start
2. **CONTRIBUTING.md** - This file
3. **API Documentation** - Docstrings in code
4. **User Guide** - Detailed usage examples
5. **Developer Guide** - Architecture and design decisions

### Writing Documentation

- Use clear, concise language
- Include code examples
- Keep it up-to-date with changes
- Test all examples

## 🤝 Community Guidelines

### Code of Conduct

We follow the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read it.

### Communication

- **GitHub Issues** - Bug reports and feature requests
- **GitHub Discussions** - General questions and ideas
- **Pull Requests** - Code contributions and reviews

### Being a Good Contributor

- **Be respectful** and inclusive
- **Help others** learn and contribute
- **Give constructive feedback**
- **Be patient** with the review process
- **Celebrate others' contributions**

## 🎯 Areas for Contribution

We welcome contributions in these areas:

### Code

- **New features** (see GitHub issues)
- **Bug fixes**
- **Performance improvements**
- **Code refactoring**
- **Test coverage improvements**

### Documentation

- **User guides** and tutorials
- **API documentation**
- **Example projects**
- **Video tutorials**

### Community

- **Answer questions** in discussions
- **Review pull requests**
- **Report bugs**
- **Share your use cases**

## 🏆 Recognition

Contributors are recognized in:

- **README.md** - Contributors section
- **CHANGELOG.md** - Release notes
- **GitHub** - Contributor graphs and statistics

## 📞 Getting Help

If you need help:

1. **Check the documentation** first
2. **Search existing issues** for similar problems
3. **Ask in GitHub Discussions** for general questions
4. **Open an issue** for bugs or specific problems

## 🙏 Thank You

Every contribution, no matter how small, makes Tskr better. Thank you for being part of our community!

---

## Happy coding! 🚀
