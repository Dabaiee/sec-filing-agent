# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-03-03

### Added
- **edgartools integration** — replaced custom SEC fetcher with edgartools library for robust XBRL, typed objects, and financial statement access
- **Hybrid XBRL + LLM analysis** — financial numbers extracted from structured XBRL data (no hallucination), LLM used only for qualitative analysis
- **Financial trend analysis** — `sec-agent trends AAPL --years 5` shows multi-year revenue, income, margins with CAGR and ASCII bar charts
- **Sector peer comparison** — `sec-agent sector AAPL` auto-detects sector and compares against peers using XBRL financial data
- **Streamlit tabs** — web app now has tabs for Single Analysis, Compare/Diff, Trends, and Sector
- 32 new tests for XBRL extraction, trend analysis, and sector comparison (total: 56 tests)

### Changed
- Analyzers (10-K, 10-Q) now use hybrid approach: XBRL for financials, LLM for risk/MD&A
- Terminal UI shows `[structured — no LLM]` for XBRL extraction stages
- README updated with "How It Works" hybrid explanation and competitor comparison table
- Version bumped to 0.3.0

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
