# 📊 SEC Filing Intelligence Agent

AI-powered analysis of SEC filings. Get structured risk assessments, financial highlights, and event summaries from 10-K, 10-Q, and 8-K filings in seconds.

```
$ sec-agent analyze AAPL

╭─────────────────────────────────────────────╮
│  SEC Filing Intelligence Agent              │
│  Analyzing: AAPL (Apple Inc.)               │
╰─────────────────────────────────────────────╯

  ✓ Fetched latest 10-K filing (2024-11-01)      0.8s
  ✓ Classified: Annual Report (10-K)              0.1s
  ✓ Routed to: 10-K Analyzer                     0.0s
  ✓ Analyzing risk factors          [sonnet]      4.2s
  ✓ Extracting financial highlights [haiku]       1.1s

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
│  Financial Highlights:                      │
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
[![CI](https://github.com/your-username/sec-filing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/your-username/sec-filing-agent/actions/workflows/ci.yml)
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
- Fetches filings directly from SEC EDGAR (no API key needed for SEC)
- Uses Claude Sonnet for complex reasoning (risk analysis, trend identification)
- Uses Claude Haiku for fast extraction (financials, metadata)
- Returns structured Pydantic models you can build on

---

## Features

| Feature | Description |
|---------|-------------|
| **Multi-stage pipeline** | Fetch → Classify → Route → Analyze → Format |
| **Smart model routing** | Sonnet for reasoning, Haiku for extraction |
| **3 filing types** | 10-K annual, 10-Q quarterly, 8-K current reports |
| **Structured output** | All LLM responses validated with Pydantic |
| **Rich terminal UI** | Spinners, progress, color-coded severity |
| **Multiple formats** | Terminal, JSON, Markdown |
| **Cost tracking** | Token usage and USD cost per request |
| **Python API** | `from sec_filing_agent import analyze` |
| **Async** | Non-blocking I/O throughout |
| **Web demo** | Streamlit app included |

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
│  │ → Sonnet     │   │ Terminal / Web    │     └────────────┘  │
│  │ Simple task  │   │                   │                      │
│  │ → Haiku      │   └───────────────────┘                      │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline Stages

1. **Fetcher** — Resolves ticker → CIK, fetches filing index from SEC EDGAR, downloads and parses the primary document
2. **Classifier** — Detects filing type (10-K, 10-Q, 8-K) using regex heuristics — no LLM call needed
3. **Router** — Dispatches to the specialized analyzer for that filing type
4. **Analyzer** — Runs multiple LLM calls with structured output (risk factors, financials, events)
5. **Model Router** — Sends complex reasoning to Sonnet ($3/M tokens), simple extraction to Haiku ($0.80/M tokens)
6. **Output Formatter** — Renders as Rich terminal panel, JSON, Markdown, or Streamlit web UI

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

# Force a specific model for all stages
sec-agent analyze AAPL --model claude-sonnet-4-20250514

# Verbose logging
sec-agent analyze AAPL --verbose
```

### Python API

```python
import asyncio
from sec_filing_agent import analyze, fetch_filing

# Analyze a filing — returns a Pydantic AnalysisReport
report = asyncio.run(analyze("AAPL", filing_type="10-K"))

print(report.summary)
print(report.financial_highlights.revenue)       # "$394.3B"
print(report.risk_factors[0].severity)           # "high"
print(report.model_usage.estimated_cost_usd)     # 0.024

# Just fetch the raw filing content
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
        try:
            report = await analyze(ticker, output_format="json")
            print(f"{report.ticker}: {report.summary[:100]}...")
        except Exception as e:
            print(f"{ticker}: Error — {e}")

asyncio.run(batch())
```

### Web Demo (Streamlit)

```bash
pip install sec-filing-agent[web]
cd web/
streamlit run app.py
```

---

## How It Works

| Filing Type | LLM Calls | What's Extracted |
|-------------|-----------|------------------|
| **10-K** (Annual) | 3 calls | Summary, risk factors (top 5 categorized), financial highlights, MD&A, forward-looking statements |
| **10-Q** (Quarterly) | 2 calls | Quarterly summary, QoQ/YoY financials, management commentary |
| **8-K** (Current) | 2 calls | Event classification, impact assessment, key figures |

Each analyzer uses structured output (JSON mode) with Pydantic validation. If validation fails, it retries once with error context appended to the prompt.

---

## Comparison

| | sec-filing-agent | Manual EDGAR | Bloomberg Terminal | SEC API wrappers |
|---|---|---|---|---|
| **Cost** | ~$0.02/query | Free (your time) | $24,000/year | Free |
| **Structured output** | Yes (Pydantic) | No | Yes | Raw data only |
| **Risk analysis** | AI-powered | Manual reading | Analyst reports | None |
| **Setup time** | 3 lines | Hours | Days | Varies |
| **Customizable** | Fully open source | N/A | No | Varies |

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

---

## Development

```bash
# Clone and install
git clone https://github.com/your-username/sec-filing-agent.git
cd sec-filing-agent
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# Run tests (24 tests, all mocked — no API key needed)
pytest

# Lint
ruff check src/ tests/

# Type check
mypy src/ --ignore-missing-imports
```

### Project Structure

```
src/sec_filing_agent/
├── __init__.py         # Public API: analyze(), fetch_filing()
├── cli.py              # Typer CLI
├── fetcher.py          # SEC EDGAR API client
├── classifier.py       # Filing type detection (heuristic)
├── router.py           # Analyzer routing
├── analyzers/          # 10-K, 10-Q, 8-K specialized analyzers
├── llm/                # LLM client, model router, prompt templates
├── models/             # Pydantic models (filing, analysis, config)
└── ui/                 # Rich terminal UI
web/
└── app.py              # Streamlit web demo
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
