# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.2.0] - 2026-03-03

### Added
- **Streamlit web demo** (`web/app.py`) — browser-based filing analysis with pipeline progress and download buttons
- **Comparison/diff mode** — `sec-agent diff` compares filings across time, `sec-agent compare` compares two companies
- **Watchlist mode** — `sec-agent watch add/remove/list/start/check/report` with SQLite storage and webhook alerts
- **Agent SDK** — `Agent` class with `analyze()`, `analyze_batch()`, `analyze_stream()`, `diff()`, `compare()` methods
- **PyPI release workflow** — GitHub Actions auto-publish on tag push with trusted publisher
- GitHub issue templates (bug report, feature request)
- Pull request template
- CONTRIBUTING.md guide
- CHANGELOG.md

### Changed
- README overhauled with hero terminal output, badges, comparison table, and comprehensive documentation
- Version bumped to 0.2.0
- `__init__.py` now exports `Agent` class

## [0.1.0] - 2026-03-02

### Added
- Initial release
- Multi-stage LLM pipeline: fetch, classify, route, analyze
- SEC EDGAR fetcher with rate limiting
- Filing type classifier (heuristic regex-based)
- Filing type router
- 10-K, 10-Q, 8-K specialized analyzers with structured output
- Smart model routing (Sonnet for reasoning, Haiku for extraction)
- Rich terminal UI with pipeline progress
- Typer CLI with `sec-agent analyze` command
- JSON and Markdown output formats
- Cost and token usage tracking
- Python API: `analyze()` and `fetch_filing()`
- 24 unit tests with mocked LLM responses
- GitHub Actions CI (lint + type check + tests)
- Examples: basic usage and batch analysis
