# Contributing to SEC Filing Intelligence Agent

Thanks for your interest in contributing! This guide will help you get started.

## Development Setup

```bash
# Clone the repo
git clone https://github.com/Dabaiee/sec-filing-agent.git
cd sec-filing-agent

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install with dev dependencies
pip install -e ".[dev]"
```

## Running Tests

Tests use mocked LLM responses — no API key needed:

```bash
pytest                    # Run all tests
pytest -v                 # Verbose output
pytest tests/test_fetcher.py  # Single test file
```

## Code Quality

```bash
# Lint
ruff check src/ tests/

# Auto-fix lint issues
ruff check src/ tests/ --fix

# Type check
mypy src/ --ignore-missing-imports
```

## Making Changes

1. **Fork** the repository and create a branch from `main`
2. **Write tests** for any new functionality
3. **Run the test suite** to make sure nothing is broken
4. **Follow existing code style** — the project uses `ruff` for linting
5. **Keep commits focused** — one logical change per commit

## Code Style

- Type hints on all public functions and methods
- Docstrings on all public classes and functions
- Line length: 100 characters
- Follow existing patterns in the codebase

## Pull Request Process

1. Update documentation if you've changed APIs or added features
2. Add tests for new functionality
3. Ensure CI passes (lint + tests)
4. Fill out the PR template
5. Request review

## Project Structure

```
src/sec_filing_agent/
├── __init__.py         # Public API exports
├── agent.py            # Agent SDK class
├── cli.py              # Typer CLI commands
├── fetcher.py          # SEC EDGAR API client
├── classifier.py       # Filing type detection
├── router.py           # Analyzer routing
├── analyzers/          # Filing-type-specific analyzers
├── diff/               # Comparison and diff features
├── llm/                # LLM client, model router, prompts
├── models/             # Pydantic data models
├── ui/                 # Rich terminal UI
└── watch/              # Watchlist monitoring
```

## Adding a New Filing Type Analyzer

1. Create `src/sec_filing_agent/analyzers/your_type.py`
2. Extend `BaseAnalyzer` from `analyzers/base.py`
3. Add prompt templates to `llm/prompts.py`
4. Register the analyzer in `router.py`
5. Add tests in `tests/test_analyzers.py`

## Questions?

Open a discussion or issue on GitHub.
