# Contributing to superreload

Thanks for your interest in contributing. This document covers the basics.

## Getting Started

1. Fork and clone the repo
2. Install dependencies: `uv sync --dev`
3. Run tests: `uv run pytest`
4. Make your changes
5. Submit a PR

## Development Setup

```bash
git clone https://github.com/YOUR_USERNAME/superreload.git
cd superreload
uv sync --dev
```

## Running Tests

```bash
uv run pytest
uv run pytest -v  # verbose
uv run pytest --cov  # with coverage
```

## Code Style

We use ruff for linting and formatting:

```bash
uv run ruff check src tests
uv run ruff format src tests
```

Type checking with mypy:

```bash
uv run mypy src
```

Pre-commit hooks run automatically on commit. If they fail, fix the issues and commit again.

## Pull Requests

1. Create a branch from `main`
2. Make focused, atomic commits
3. Use conventional commit format (see below)
4. Add tests for new functionality
5. Ensure all tests pass
6. Ensure linting passes
7. Submit PR with a clear description of changes

## Commit Messages

We use [Conventional Commits](https://www.conventionalcommits.org/). Format: `type: description`

| Type | Use For |
|------|---------|
| `feat` | New features |
| `fix` | Bug fixes |
| `docs` | Documentation only |
| `refactor` | Code changes that don't fix bugs or add features |
| `test` | Adding/updating tests |
| `ci` | CI/CD changes |
| `chore` | Maintenance (deps, configs) |

**Rules:**
- Commit each logical change separately (not batched)
- Commit immediately when a change is complete and working
- Keep commits atomic - one concern per commit
- Run tests before committing

**Examples:**
```
feat: add Flask framework support
fix: CSS hot reload closure bug
docs: update installation instructions
refactor: extract WebSocket handler into separate class
test: add integration tests for Django middleware
ci: add Python 3.13 to test matrix
```

### PR Guidelines

- Keep PRs focused on a single change
- Update documentation if needed
- Add tests for bug fixes and new features
- Don't break existing functionality

## Bug Reports

Open an issue with:

- What you expected
- What happened
- Steps to reproduce
- Python version, Django version, OS

## Feature Requests

Open an issue describing:

- The problem you're trying to solve
- Your proposed solution
- Alternatives you've considered

## Code of Conduct

Be professional. Be respectful. Focus on the code and the work. We're here to build good software.

## License

By contributing, you agree that your contributions will be licensed under the MIT License.
