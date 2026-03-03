# SEC Filing Intelligence Agent

AI-powered analysis of SEC filings. Get structured risk assessments, financial highlights, and event summaries from 10-K, 10-Q, and 8-K filings in seconds.

<!-- DEMO GIF: Record with `asciinema rec demo.cast && asciinema-agg demo.cast demo.gif` -->
<!-- ![Demo](assets/demo.gif) -->
> Demo GIF coming soon — run `sec-agent analyze AAPL` to see it in action

[![PyPI](https://img.shields.io/pypi/v/sec-filing-agent)](https://pypi.org/project/sec-filing-agent/)
[![Python](https://img.shields.io/pypi/pyversions/sec-filing-agent)](https://pypi.org/project/sec-filing-agent/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![CI](https://github.com/Dabaiee/sec-filing-agent/actions/workflows/ci.yml/badge.svg)](https://github.com/Dabaiee/sec-filing-agent/actions)
<!-- [![Try Live Demo](https://img.shields.io/badge/demo-streamlit-FF4B4B)](https://your-app.streamlit.app) -->

## Quick Start

```bash
pip install sec-filing-agent
export ANTHROPIC_API_KEY=sk-ant-...
sec-agent analyze AAPL
```

## Features

- **Hybrid XBRL + LLM** — Financial numbers from XBRL structured data (never hallucinated), AI for qualitative analysis
- **Multi-filing support** — 10-K annual reports, 10-Q quarterly reports, 8-K current events
- **Structured output** — Pydantic-validated JSON, not free-text LLM responses
- **Model routing** — Sonnet for complex analysis, Haiku for classification (cost-optimized)
- **Beautiful terminal UI** — Rich-powered progress tracking and formatted reports
- **Python SDK** — `from sec_filing_agent import Agent` for programmatic use
- **Multiple output formats** — Terminal, JSON, Markdown
- **Trend analysis** — Multi-year financial trends with CAGR
- **Sector comparison** — Peer benchmarking with auto-detected sector peers
- **Filing diff** — Compare filings across time periods or companies
- **Watchlist** — Monitor tickers for new filings with webhook alerts

## How It Works

```
SEC EDGAR ──→ Fetch Filing ──→ Classify Type ──→ Route to Analyzer
                                                       │
                                 ┌─────────────────────────────────┐
                                 │  Hybrid Analysis Pipeline       │
                                 │                                 │
                                 │  XBRL: revenue, margins, EPS   │
                                 │        (structured — no LLM)   │
                                 │            ↓                    │
                                 │  Sonnet: risk factors, MD&A    │
                                 │          (complex reasoning)    │
                                 │            ↓                    │
                                 │  Haiku: classification,        │
                                 │         extraction (fast/cheap) │
                                 │            ↓                    │
                                 │  Pydantic: validate output     │
                                 │            (retry if invalid)   │
                                 └─────────────────────────────────┘
                                                       │
                                 Structured Report (JSON / Terminal / Markdown)
```

### Why not just use ChatGPT?

| | sec-filing-agent | Paste into ChatGPT |
|---|---|---|
| Financial numbers | From XBRL — **never hallucinated** | LLM extraction — can hallucinate |
| Output format | Structured JSON with schema | Free text |
| Cost per analysis | ~$0.02 (model routing) | ~$0.10+ (GPT-4 for everything) |
| Reproducible | Same input → same schema | Different every time |
| Automation-friendly | CLI + Python API | Manual copy-paste |

## Usage

### CLI

```bash
# Analyze latest filing
sec-agent analyze AAPL

# Specific filing type
sec-agent analyze MSFT --filing-type 10-K
sec-agent analyze AAPL --filing-type 10-Q
sec-agent analyze TSLA --filing-type 8-K

# JSON output for automation
sec-agent analyze NVDA --output json

# Markdown for reports
sec-agent analyze TSLA --output markdown

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
```

### Python API

```python
from sec_filing_agent import Agent

agent = Agent()
report = await agent.analyze("AAPL", filing_type="10-K")

print(report.summary)
print(report.risk_factors[0].severity)     # "high"
print(report.financial_highlights.revenue)  # "$394.3B"
print(report.model_usage.estimated_cost_usd)  # 0.024
```

## Configuration

| Env Variable | Required | Description |
|---|---|---|
| `ANTHROPIC_API_KEY` | Yes | Anthropic API key |
| `OPENAI_API_KEY` | No | OpenAI fallback |
| `SEC_AGENT_MODEL` | No | Force specific model |
| `SEC_AGENT_USER_AGENT` | No | SEC EDGAR User-Agent header |

## Example Output

```
╭─ Analysis Report ──────────────────────────────╮
│                                                 │
│  AAPL — Apple Inc.                              │
│  10-K Annual Report | Filed: 2024-11-01         │
│                                                 │
│  Summary: Apple reported revenue of $394.3B...  │
│                                                 │
│  Risk Factors:                                  │
│  ● HIGH: Global supply chain concentration...   │
│  ● MED: Regulatory scrutiny in EU and US...     │
│                                                 │
│  Financial Highlights (from XBRL):              │
│  Revenue      $394.3B   +2.0%                   │
│  Net Income   $93.7B    -3.4%                   │
│  Gross Margin 46.2%     +0.8pp                  │
│                                                 │
│  Sonnet: 3,420 tok · Haiku: 1,205 tok           │
│  Cost: $0.024 · Duration: 12.3s                 │
╰─────────────────────────────────────────────────╯
```

## Comparison

| Feature | sec-filing-agent | sec-insights | 10K-Analyzer | sec-edgar-agentkit |
|---------|-----------------|--------------|--------------|-------------------|
| CLI tool | Yes | No | No | No |
| Structured JSON output | Yes | No | No | No |
| XBRL financial data | Yes | No | No | Yes |
| Hallucination-free numbers | Yes | No | No | No |
| Model routing (cost opt.) | Yes | No | No | No |
| Multi-filing type | Yes | Yes | 10-K only | Yes |
| Trend analysis | Yes | No | No | No |
| Sector comparison | Yes | No | No | No |
| Filing diff / compare | Yes | No | No | No |
| pip install | Yes | No | No | Yes |

## Architecture

```
src/sec_filing_agent/
├── __init__.py         # Public API: Agent, analyze(), fetch_filing()
├── cli.py              # Typer CLI (analyze, trends, sector, diff, compare, watch)
├── agent.py            # Agent SDK class
├── fetcher.py          # SEC EDGAR data via edgartools (with TTL cache)
├── classifier.py       # Filing type detection (heuristic, no LLM)
├── router.py           # Analyzer registry and routing
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
```

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for development setup and guidelines.

## License

MIT — see [LICENSE](LICENSE) for details.
