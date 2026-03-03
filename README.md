# 📊 SEC Filing Intelligence Agent

AI-powered analysis of SEC filings with **hybrid XBRL + LLM** approach. Financial numbers from structured data — never hallucinated. Qualitative analysis from AI.

```
$ sec-agent analyze AAPL

╭─────────────────────────────────────────────╮
│  SEC Filing Intelligence Agent              │
│  Analyzing: AAPL (Apple Inc.)               │
╰─────────────────────────────────────────────╯

  ✓ Fetched latest 10-K filing (2024-11-01)      0.8s
  ✓ Classified: Annual Report (10-K)              0.1s
  ✓ Routed to: 10-K Analyzer                     0.0s
  ✓ Financial data extracted from XBRL  [structured — no LLM]   0.3s
  ✓ Analyzing risk factors              [sonnet]                 4.2s
  ✓ Extracting management discussion    [sonnet]                 3.1s
  ✓ Forward-looking statements          [haiku]                  1.1s

╭─ Analysis Report ───────────────────────────╮
│  AAPL — Apple Inc.                          │
│  10-K Annual Report | Filed: 2024-11-01     │
│                                             │
│  Summary:                                   │
│  Apple reported $394B revenue, up 2% YoY... │
│                                             │
│  Top Risk Factors:                          │
│  🔴 HIGH: Global supply chain disruption    │
│  🟡 MED: Regulatory scrutiny in EU          │
│  🟡 MED: Competition in AI/ML space         │
│                                             │
│  Financial Highlights (from XBRL):          │
│  Revenue      $394.3B   +2.0%               │
│  Net Income   $93.7B    -3.4%               │
│  Gross Margin 46.2%     +0.8pp              │
│                                             │
│  Sonnet: 3,420 tokens · Haiku: 1,205 tokens │
│  Estimated cost: $0.024                     │
╰─────────────────────────────────────────────╯
```

[![PyPI](https://img.shields.io/pypi/v/sec-filing-agent.svg)](https://pypi.org/project/sec-filing-agent/)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![CI](https://github.com/Dabaiee/sec-filing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Dabaiee/sec-filing-agent/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

---

## Quick Start

```bash
pip install sec-filing-agent
export ANTHROPIC_API_KEY=sk-ant-...
sec-agent analyze AAPL
```

That's it. Three lines to get a structured analysis of Apple's latest SEC filing.

---

## Why This Exists

Reading SEC filings manually is slow and painful. Bloomberg terminals cost $24k/year. This tool gives you structured, AI-powered analysis of any public company's SEC filings from your terminal — for pennies per query.

**What it does:**
- Fetches filings from SEC EDGAR using [edgartools](https://github.com/dgunning/edgartools) — the best SEC data library
- Extracts financial numbers from **XBRL structured data** — 100% accurate, no LLM hallucination
- Uses Claude Sonnet for complex reasoning (risk analysis, trend identification)
- Uses Claude Haiku for fast extraction (metadata, forward-looking statements)
- Returns structured Pydantic models you can build on

---

## How It Works

Unlike other SEC analysis tools that use LLM for everything (including financial number extraction), sec-filing-agent uses a **hybrid approach**:

| Data Type | Source | Why |
|-----------|--------|-----|
| Financial numbers (revenue, margins, EPS) | XBRL structured data via edgartools | 100% accurate, no hallucination |
| Risk factors, MD&A, forward-looking | LLM analysis (Claude) | Qualitative reasoning is LLM's strength |
| Multi-year trends | XBRL historical facts | Real data, computed metrics |
| Executive summary | LLM synthesis | Combines structured + qualitative |

This means financial numbers in our reports are **never hallucinated** — they come directly from SEC XBRL filings. LLM is used only where it adds value: understanding, summarization, and reasoning.

```
  ✓ Financial data extracted from XBRL     [structured — no LLM]
  ✓ Risk factors analyzed                  [claude-sonnet]
  ✓ Management discussion analyzed         [claude-sonnet]
  ✓ Forward-looking statements extracted   [claude-haiku]
```

---

## Features

| Feature | Description |
|---------|-------------|
| **Hybrid XBRL + LLM** | Structured data for numbers, AI for qualitative analysis |
| **Multi-stage pipeline** | Fetch → Classify → Route → Analyze → Format |
| **Smart model routing** | Sonnet for reasoning, Haiku for extraction |
| **3 filing types** | 10-K annual, 10-Q quarterly, 8-K current reports |
| **Trend analysis** | Multi-year financial trends with CAGR and ASCII charts |
| **Sector comparison** | Peer benchmarking with auto-detected sector peers |
| **Filing diff** | Compare filings across time periods |
| **Company comparison** | Compare two companies' filings head-to-head |
| **Watchlist** | Monitor tickers for new filings with webhook alerts |
| **Structured output** | All LLM responses validated with Pydantic |
| **Rich terminal UI** | Spinners, progress, color-coded severity |
| **Multiple formats** | Terminal, JSON, Markdown |
| **Cost tracking** | Token usage and USD cost per request |
| **Python Agent SDK** | `Agent` class with streaming, batch, diff, compare |
| **Web demo** | Streamlit app with tabs for all features |

---

## Comparison

| Feature | sec-filing-agent | sec-insights | 10K-Analyzer | sec-edgar-agentkit |
|---------|-----------------|--------------|--------------|-------------------|
| CLI tool | Yes | No | No | No |
| Structured JSON output | Yes | No | No | No |
| XBRL financial data | Yes | No | No | Yes |
| Hallucination-free numbers | Yes | No | No | No |
| Model routing (cost optimization) | Yes | No | No | No |
| Multi-filing type (10-K/10-Q/8-K) | Yes | Yes | 10-K only | Yes |
| Trend analysis | Yes | No | No | No |
| Sector comparison | Yes | No | No | No |
| Filing diff / compare | Yes | No | No | No |
| pip install | Yes | No | No | Yes |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    SEC Filing Intelligence Agent                 │
│                                                                 │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────────┐  │
│  │ Fetcher  │──▶│Classifier│──▶│ Router   │──▶│ Analyzers  │  │
│  │          │   │          │   │          │   │            │  │
│  │edgartools│   │ Detect   │   │ Route to │   │ ┌────────┐ │  │
│  │  XBRL +  │   │ filing   │   │ correct  │   │ │10-K    │ │  │
│  │ filings  │   │ type     │   │ analyzer │   │ │Analyzer│ │  │
│  └──────────┘   └──────────┘   └──────────┘   │ ├────────┤ │  │
│                                                │ │10-Q    │ │  │
│                                                │ │Analyzer│ │  │
│  ┌──────────────┐   ┌───────────────────┐     │ ├────────┤ │  │
│  │ Model Router │   │ Output Formatter  │     │ │8-K     │ │  │
│  │              │   │                   │     │ │Analyzer│ │  │
│  │ Complex task │   │ JSON / Markdown / │     │ └────────┘ │  │
│  │ → Sonnet     │   │ Terminal / Web    │     └────────────┘  │
│  │ Simple task  │   │                   │                      │
│  │ → Haiku      │   └───────────────────┘                      │
│  └──────────────┘                                              │
│                                                                 │
│  Hybrid Analysis:                                               │
│  ┌──────────────────┐  ┌──────────────────────┐               │
│  │ XBRL Structured  │  │ LLM Qualitative      │               │
│  │ ──────────────── │  │ ──────────────────── │               │
│  │ Revenue, margins │  │ Risk factors, MD&A   │               │
│  │ EPS, trends      │  │ Forward-looking      │               │
│  │ Peer metrics     │  │ Executive summary    │               │
│  │ (no hallucination│  │ (AI reasoning)       │               │
│  └──────────────────┘  └──────────────────────┘               │
└─────────────────────────────────────────────────────────────────┘
```

---

## Usage

### CLI

```bash
# Analyze the latest filing for a ticker
sec-agent analyze AAPL

# Specify a filing type
sec-agent analyze MSFT --filing-type 10-K
sec-agent analyze AAPL --filing-type 10-Q
sec-agent analyze TSLA --filing-type 8-K

# Output formats
sec-agent analyze AAPL --output json       # Machine-readable JSON
sec-agent analyze AAPL --output markdown   # Markdown report
sec-agent analyze AAPL --output terminal   # Rich terminal UI (default)

# Multi-year financial trends
sec-agent trends AAPL --years 5

# Sector peer comparison
sec-agent sector AAPL
sec-agent sector AAPL --peers MSFT GOOG META

# Compare filings across time
sec-agent diff AAPL --filing-type 10-K --from 2023 --to 2024

# Compare two companies
sec-agent compare AAPL MSFT --filing-type 10-K

# Watchlist
sec-agent watch add AAPL MSFT NVDA
sec-agent watch start --interval 60 --webhook https://hooks.slack.com/...
sec-agent watch check
sec-agent watch report

# Force a specific model
sec-agent analyze AAPL --model claude-sonnet-4-20250514

# Verbose logging
sec-agent analyze AAPL --verbose
```

### Python API

```python
import asyncio
from sec_filing_agent import Agent

# Create an agent
agent = Agent()

# Analyze a filing — returns a Pydantic AnalysisReport
report = asyncio.run(agent.analyze("AAPL", filing_type="10-K"))

print(report.summary)
print(report.financial_highlights.revenue)       # "$394.3B"
print(report.risk_factors[0].severity)           # "high"
print(report.model_usage.estimated_cost_usd)     # 0.024

# Batch analysis
reports = asyncio.run(agent.analyze_batch(["AAPL", "MSFT", "GOOGL"]))

# Streaming
async for event in agent.analyze_stream("AAPL"):
    print(f"[{event.stage}] {event.message}")

# Diff and compare
diff = asyncio.run(agent.diff("AAPL", from_period="2023", to_period="2024"))
comparison = asyncio.run(agent.compare("AAPL", "MSFT"))
```

### Web Demo (Streamlit)

```bash
pip install sec-filing-agent[web]
cd web/
streamlit run app.py
```

The web app includes tabs for Single Analysis, Compare/Diff, Trends, and Sector.

---

## Configuration

### Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `OPENAI_API_KEY` | No | Optional OpenAI fallback |
| `SEC_AGENT_MODEL` | No | Force a specific model for all stages |
| `SEC_AGENT_USER_AGENT` | No | User-Agent for SEC EDGAR (default provided) |

### Model Routing

| Task Complexity | Model | Cost | Examples |
|----------------|-------|------|----------|
| High | Claude Sonnet | $3.00 / $15.00 per M tokens | Risk analysis, financial reasoning, event assessment |
| Low | Claude Haiku | $0.80 / $4.00 per M tokens | Classification, data extraction, summarization |
| None | XBRL structured | Free | Financial numbers, margins, EPS, trends |

---

## Development

```bash
# Clone and install
git clone https://github.com/Dabaiee/sec-filing-agent.git
cd sec-filing-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (56 tests, all mocked — no API key needed)
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

### Project Structure

```
src/sec_filing_agent/
├── __init__.py         # Public API: Agent, analyze(), fetch_filing()
├── cli.py              # Typer CLI (analyze, trends, sector, diff, compare, watch)
├── agent.py            # Agent SDK class
├── fetcher.py          # SEC EDGAR data via edgartools
├── classifier.py       # Filing type detection (heuristic)
├── router.py           # Analyzer routing
├── sector.py           # Sector peer comparison
├── trends.py           # Multi-year trend analysis
├── analyzers/
│   ├── xbrl.py         # XBRL financial extraction (no LLM)
│   ├── ten_k.py        # 10-K hybrid analyzer (XBRL + LLM)
│   ├── ten_q.py        # 10-Q hybrid analyzer (XBRL + LLM)
│   └── eight_k.py      # 8-K analyzer (LLM only — event-driven)
├── diff/               # Filing diff and company comparison
├── watch/              # Watchlist with SQLite + webhook alerts
├── llm/                # LLM client, model router, prompt templates
├── models/             # Pydantic models (filing, analysis, config, trends, sector)
└── ui/                 # Rich terminal UI
web/
└── app.py              # Streamlit web demo (all features)
```

---

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest`) and linter (`ruff check src/ tests/`)
5. Commit with a descriptive message
6. Push and open a Pull Request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

---

## License

MIT License. See [LICENSE](LICENSE) for details.
