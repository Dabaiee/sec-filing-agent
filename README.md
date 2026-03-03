# SEC Filing Intelligence Agent

AI-powered SEC filing analysis using multi-stage LLM pipelines.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)
[![CI](https://github.com/your-username/sec-filing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/sec-filing-agent/actions/workflows/ci.yml)

---

## Quick Start

```bash
# Install
pip install sec-filing-agent

# Set your API key
export ANTHROPIC_API_KEY=sk-ant-...

# Analyze a filing
sec-agent analyze AAPL
sec-agent analyze MSFT --filing-type 10-Q
sec-agent analyze TSLA --output json
```

---

## Features

- **Multi-stage LLM pipeline** — Fetch, classify, route, and analyze SEC filings
- **Smart model routing** — Complex reasoning (Sonnet) vs. simple extraction (Haiku)
- **Structured output** — All LLM responses validated with Pydantic models
- **3 filing types** — 10-K annual reports, 10-Q quarterly reports, 8-K current reports
- **Rich terminal UI** — Pipeline progress with spinners, checkmarks, and per-stage model labels
- **Multiple output formats** — Terminal (Rich), JSON, Markdown
- **Cost tracking** — Token usage and estimated cost per request
- **Python API** — Use as a library: `from sec_filing_agent import analyze`
- **Async throughout** — Fetcher and LLM calls are fully async

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEC Filing Intelligence Agent                 │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐  │
│  │ Fetcher  │──▶│Classifier│──▶│ Router   │──▶│ Analyzers  │  │
│  │          │   │          │   │          │   │            │  │
│  │ SEC EDGAR│   │ Detect   │   │ Route to │   │ ┌────────┐ │  │
│  │ API call │   │ filing   │   │ correct  │   │ │10-K    │ │  │
│  │ + parse  │   │ type     │   │ analyzer │   │ │Analyzer│ │  │
│  └──────────┘   └──────────┘   └──────────┘   │ ├────────┤ │  │
│                                                │ │10-Q    │ │  │
│                                                │ │Analyzer│ │  │
│  ┌──────────────┐   ┌───────────────────┐     │ ├────────┤ │  │
│  │ Model Router │   │ Output Formatter  │     │ │8-K     │ │  │
│  │              │   │                   │     │ │Analyzer│ │  │
│  │ Complex task │   │ JSON / Markdown / │     │ └────────┘ │  │
│  │ → Sonnet     │   │ Terminal Rich UI  │     └────────────┘  │
│  │ Simple task  │   │                   │                      │
│  │ → Haiku      │   └───────────────────┘                      │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

1. **Fetcher** — Hit SEC EDGAR API to get filings for a ticker
2. **Classifier** — Determine filing type (10-K, 10-Q, 8-K) and extract metadata
3. **Router** — Route to the correct specialized analyzer
4. **Analyzer** — Extract key data and generate analysis using LLM
5. **Model Router** — Send complex reasoning to Sonnet, simple extraction to Haiku
6. **Output Formatter** — Format as JSON, Markdown, or Rich terminal UI

---

## Usage

### CLI

```bash
# Basic usage — analyzes the latest filing
sec-agent analyze AAPL

# Specific filing type
sec-agent analyze MSFT --filing-type 10-K
sec-agent analyze AAPL --filing-type 10-Q
sec-agent analyze TSLA --filing-type 8-K

# Output formats
sec-agent analyze AAPL --output json       # Machine-readable JSON
sec-agent analyze AAPL --output markdown   # Markdown report
sec-agent analyze AAPL --output terminal   # Rich terminal UI (default)

# Force a specific model
sec-agent analyze AAPL --model claude-sonnet-4-20250514

# Verbose logging
sec-agent analyze AAPL --verbose
```

### Python API

```python
import asyncio
from sec_filing_agent import analyze, fetch_filing

# Analyze a filing
report = asyncio.run(analyze("AAPL", filing_type="10-K"))
print(report.summary)
print(report.financial_highlights.revenue)

# Just fetch the raw filing
filing = asyncio.run(fetch_filing("AAPL"))
print(filing.content[:500])
```

### Batch Analysis

```python
import asyncio
from sec_filing_agent import analyze

async def batch():
    tickers = ["AAPL", "MSFT", "GOOGL", "NVDA"]
    for ticker in tickers:
        report = await analyze(ticker, output_format="json")
        print(f"{report.ticker}: {report.summary}")

asyncio.run(batch())
```

---

## How It Works

1. **Fetch**: The agent queries SEC EDGAR's company submissions API to find the latest filing for a given ticker. It resolves the ticker to a CIK (Central Index Key), fetches the filing index, and downloads the primary document.

2. **Classify**: The classifier uses regex heuristics to detect the filing type (10-K, 10-Q, 8-K) and extracts metadata like the period of report. No LLM call needed for this step.

3. **Route**: Based on the filing type, the router selects the appropriate specialized analyzer.

4. **Analyze**: The analyzer runs multiple LLM calls with structured output:
   - **10-K**: Summary + risk factors (Sonnet) + financial extraction (Haiku)
   - **10-Q**: Quarterly summary (Sonnet) + financial extraction (Haiku)
   - **8-K**: Event analysis (Sonnet) + financial extraction (Haiku)

5. **Format**: The output formatter renders the structured report as a Rich terminal panel, JSON, or Markdown.

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `OPENAI_API_KEY` | No | Optional OpenAI fallback |
| `SEC_AGENT_MODEL` | No | Force a specific model for all stages |
| `SEC_AGENT_USER_AGENT` | No | User-Agent for SEC EDGAR (default: `SEC-Filing-Agent admin@example.com`) |

### Model Routing

| Task Type | Model | Examples |
|-----------|-------|----------|
| High complexity | Claude Sonnet | Risk analysis, financial reasoning, event assessment |
| Low complexity | Claude Haiku | Filing classification, data extraction, summarization |

---

## Development

```bash
# Clone and install
git clone https://github.com/your-username/sec-filing-agent.git
cd sec-filing-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests (`pytest`)
5. Commit (`git commit -m 'Add amazing feature'`)
6. Push (`git push origin feature/amazing-feature`)
7. Open a Pull Request

---

## License

MIT License. See [LICENSE](LICENSE) for details.
