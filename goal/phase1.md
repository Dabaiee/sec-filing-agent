# SEC Filing Intelligence Agent — Complete Build Prompt

## Setup & Ralph Loop

```bash
# 1. Create project and init
mkdir -p ~/workspace/sec-filing-agent && cd ~/workspace/sec-filing-agent
git init
cp ~/workspace/JobHunter/sec-filing-agent-prompt.md CLAUDE.md

# 2. Open Claude Code in the project
cd ~/workspace/sec-filing-agent
claude
```

Once Claude Code opens, paste this as your first message:

```
Read CLAUDE.md. This is the full spec for the project. Build it from Phase 1 to Phase 9 following the implementation order exactly. After each phase, commit with a meaningful message. Do not ask me questions — make reasonable decisions and keep building. Start now.
```

Then run `/ralph-loop` to keep it going autonomously.

---

## Project: SEC Filing Intelligence Agent

Build an open-source Python CLI tool and library called `sec-filing-agent` that fetches SEC EDGAR filings, classifies them, extracts key financial data, and generates structured analysis reports using LLM-powered multi-stage pipelines.

This project exists to demonstrate production AI engineering skills: multi-stage LLM pipelines, structured output validation, model routing, and clean open-source packaging.

---

## Core User Stories

```
1. As a user, I can run `sec-agent analyze AAPL` and get a structured analysis of Apple's latest SEC filing
2. As a user, I can run `sec-agent analyze AAPL --filing-type 10-K` to analyze a specific filing type
3. As a user, I can run `sec-agent analyze AAPL --output json` to get machine-readable structured output
4. As a developer, I can `from sec_filing_agent import analyze` and use it as a Python library
5. As a user, I can see a streaming terminal UI showing each pipeline stage as it processes
```

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
│  │ → Claude 3.5 │   │ Terminal Rich UI  │     └────────────┘  │
│  │ Simple task  │   │                   │                      │
│  │ → Haiku      │   └───────────────────┘                      │
│  └──────────────┘                                              │
└─────────────────────────────────────────────────────────────────┘
```

### Pipeline stages:
1. **Fetcher** — Hit SEC EDGAR FULL-TEXT SEARCH API to get filings for a ticker
2. **Classifier** — Determine filing type (10-K, 10-Q, 8-K) and extract metadata
3. **Router** — Route to the correct specialized analyzer based on filing type
4. **Analyzer** (filing-type-specific) — Extract key data + generate analysis using LLM
5. **Model Router** — Send complex reasoning to Claude Sonnet, simple extraction to Haiku
6. **Output Formatter** — Format as JSON, Markdown, or Rich terminal UI

---

## Tech Stack

- **Language:** Python 3.11+
- **LLM:** Anthropic Claude API (primary), with OpenAI as optional fallback
- **SEC Data:** SEC EDGAR APIs (NO API KEY REQUIRED, but must set User-Agent header per SEC policy):
  - Company tickers: `https://www.sec.gov/files/company_tickers.json`
  - Company filings index: `https://data.sec.gov/submissions/CIK{cik_zero_padded_10_digits}.json`
  - Full-text search: `https://efts.sec.gov/LATEST/search-index?q={query}&forms={form_type}`
  - Filing documents: URLs returned in the submissions JSON `recentFilings` field
- **CLI Framework:** `typer` (modern, type-hint based CLI)
- **Terminal UI:** `rich` (tables, progress bars, panels, streaming output)
- **HTTP:** `httpx` (async support)
- **Structured Output:** `pydantic` for all data models and LLM output validation
- **Package Manager:** `uv` (fast Python package manager)
- **Testing:** `pytest` + `pytest-asyncio`

---

## File Structure

```
sec-filing-agent/
├── pyproject.toml              # Package config, dependencies, entry points
├── README.md                   # Comprehensive README with badges, examples, architecture diagram
├── LICENSE                     # MIT
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions: lint + test + type check
├── src/
│   └── sec_filing_agent/
│       ├── __init__.py         # Public API: analyze(), fetch_filing()
│       ├── cli.py              # Typer CLI: sec-agent analyze <ticker>
│       ├── fetcher.py          # SEC EDGAR API client
│       ├── classifier.py       # Filing type classification
│       ├── router.py           # Route to correct analyzer
│       ├── analyzers/
│       │   ├── __init__.py
│       │   ├── base.py         # Base analyzer interface
│       │   ├── ten_k.py        # 10-K annual report analyzer
│       │   ├── ten_q.py        # 10-Q quarterly report analyzer
│       │   └── eight_k.py      # 8-K current report analyzer
│       ├── llm/
│       │   ├── __init__.py
│       │   ├── client.py       # LLM client abstraction (Claude/OpenAI)
│       │   ├── model_router.py # Route tasks to appropriate model tier
│       │   └── prompts.py      # All prompt templates
│       ├── models/
│       │   ├── __init__.py
│       │   ├── filing.py       # Pydantic models: Filing, FilingMetadata
│       │   ├── analysis.py     # Pydantic models: AnalysisReport, RiskFactors, Financials
│       │   └── config.py       # Configuration model
│       └── ui/
│           ├── __init__.py
│           └── terminal.py     # Rich terminal UI: progress, panels, streaming
├── tests/
│   ├── conftest.py             # Fixtures: sample filings, mock LLM responses
│   ├── test_fetcher.py
│   ├── test_classifier.py
│   ├── test_router.py
│   ├── test_analyzers.py
│   └── test_cli.py
└── examples/
    ├── basic_usage.py          # Simple Python API usage
    └── batch_analysis.py       # Analyze multiple tickers
```

---

## Detailed Specs

### 1. SEC EDGAR Fetcher (`fetcher.py`)

```python
# Must set User-Agent header per SEC EDGAR policy:
# "CompanyName AdminEmail" e.g. "SEC-Filing-Agent admin@example.com"

# Endpoints:
# Company tickers: https://www.sec.gov/files/company_tickers.json → find CIK for ticker
# Company filings: https://data.sec.gov/submissions/CIK{cik_zero_padded}.json → get filing list
# Filing document: parse the primaryDocument URL from filings list, fetch from https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{primaryDocument}

# Key functions:
async def fetch_latest_filing(ticker: str, filing_type: str | None = None) -> RawFiling
async def fetch_filings(ticker: str, limit: int = 5) -> list[RawFiling]
```

- Use `httpx.AsyncClient` for all HTTP calls
- Respect SEC rate limit: max 10 requests/second
- Parse the filing index page to find the actual document URL
- Extract the raw text content from the filing HTML
- Handle edge cases: company not found, no filings of that type, rate limited

### 2. Classifier (`classifier.py`)

```python
# Determine filing type and extract metadata
# This is a LIGHTWEIGHT operation — use regex/heuristics first, LLM only if ambiguous

def classify_filing(raw: RawFiling) -> FilingMetadata
# Returns: filing_type (10-K, 10-Q, 8-K), company_name, ticker, filing_date, period_of_report, cik
```

- Try regex/heuristic classification first (form type is usually in the filing header)
- Fall back to Haiku for ambiguous cases (cost-efficient)

### 3. Router (`router.py`)

```python
# Route to the correct analyzer based on filing type

def get_analyzer(filing_type: str) -> BaseAnalyzer
# Returns: TenKAnalyzer, TenQAnalyzer, or EightKAnalyzer
```

### 4. Analyzers (`analyzers/`)

Each analyzer implements a common interface:

```python
class BaseAnalyzer(ABC):
    @abstractmethod
    async def analyze(self, filing: RawFiling, metadata: FilingMetadata) -> AnalysisReport:
        ...
```

**10-K Analyzer** extracts:
- Business overview summary
- Key risk factors (top 5, categorized)
- Financial highlights (revenue, net income, margins, YoY changes)
- Management discussion key points
- Forward-looking statements

**10-Q Analyzer** extracts:
- Quarterly financial highlights
- QoQ and YoY comparisons
- Material changes flagged
- Management commentary highlights

**8-K Analyzer** extracts:
- Event type classification (earnings, M&A, leadership change, etc.)
- Event summary
- Material impact assessment
- Key figures/data points

### 5. Model Router (`llm/model_router.py`)

```python
# Core concept: route based on task complexity

class ModelRouter:
    def route(self, task: LLMTask) -> ModelConfig:
        if task.complexity == "high":    # financial reasoning, risk analysis, correlation
            return ModelConfig(model="claude-sonnet-4-20250514", max_tokens=4096)
        else:                            # classification, extraction, summarization
            return ModelConfig(model="claude-haiku-4-5-20251001", max_tokens=2048)

# Tasks tagged with complexity:
# HIGH: risk factor analysis, financial trend reasoning, forward-looking assessment
# LOW: filing type classification, entity extraction, section identification, basic summarization
```

- Track token usage and cost per request
- Log which model handled which task (for the terminal UI to show)
- Support env var override: `SEC_AGENT_MODEL=claude-sonnet-4-20250514` to force a specific model

### 6. Pydantic Output Models (`models/`)

```python
class AnalysisReport(BaseModel):
    ticker: str
    company_name: str
    filing_type: str  # "10-K", "10-Q", "8-K"
    filing_date: date
    period_of_report: str
    summary: str  # 2-3 sentence executive summary

    # Filing-type-specific sections (optional, filled based on type)
    risk_factors: list[RiskFactor] | None = None
    financial_highlights: FinancialHighlights | None = None
    key_events: list[KeyEvent] | None = None
    management_discussion: str | None = None
    forward_looking: list[str] | None = None

    # Metadata
    model_usage: ModelUsage  # which models were used, tokens, estimated cost
    pipeline_duration_ms: int

class RiskFactor(BaseModel):
    category: str  # "regulatory", "market", "operational", "financial", "competitive"
    title: str
    description: str
    severity: str  # "high", "medium", "low"

class FinancialHighlights(BaseModel):
    revenue: str | None = None
    net_income: str | None = None
    gross_margin: str | None = None
    operating_margin: str | None = None
    yoy_revenue_change: str | None = None
    key_metrics: dict[str, str] = {}

class KeyEvent(BaseModel):
    event_type: str  # "earnings", "acquisition", "leadership", "restructuring", "other"
    headline: str
    details: str
    material_impact: str  # "high", "medium", "low"

class ModelUsage(BaseModel):
    stages: list[StageUsage]
    total_input_tokens: int
    total_output_tokens: int
    estimated_cost_usd: float

class StageUsage(BaseModel):
    stage: str
    model: str
    input_tokens: int
    output_tokens: int
```

All LLM calls must use structured output (Anthropic tool_use / json mode) and validate against these Pydantic models. On validation failure, retry once with error context appended to prompt.

### 7. Terminal UI (`ui/terminal.py`)

Use `rich` library to create a polished terminal experience:

```
$ sec-agent analyze AAPL

╭─────────────────────────────────────────────╮
│  SEC Filing Intelligence Agent              │
│  Analyzing: AAPL (Apple Inc.)               │
╰─────────────────────────────────────────────╯

  ✓ Fetched latest 10-K filing (2024-11-01)      0.8s
  ✓ Classified: Annual Report (10-K)              0.1s
  ✓ Routed to: 10-K Analyzer                     0.0s
  ◐ Analyzing risk factors...                [claude-sonnet]
  ◐ Extracting financial highlights...       [claude-haiku]

╭─ Analysis Report ───────────────────────────╮
│                                             │
│  AAPL — Apple Inc.                          │
│  10-K Annual Report | Filed: 2024-11-01     │
│                                             │
│  Summary:                                   │
│  Apple reported $394B revenue, up 2% YoY... │
│                                             │
│  Top Risk Factors:                          │
│  🔴 HIGH: Global supply chain disruption... │
│  🟡 MED: Regulatory scrutiny in EU...       │
│  🟡 MED: Competition in AI/ML space...      │
│                                             │
│  Financial Highlights:                      │
│  ┌──────────────┬──────────┬─────────┐      │
│  │ Metric       │ Value    │ YoY     │      │
│  ├──────────────┼──────────┼─────────┤      │
│  │ Revenue      │ $394.3B  │ +2.0%   │      │
│  │ Net Income   │ $93.7B   │ -3.4%   │      │
│  │ Gross Margin │ 46.2%    │ +0.8pp  │      │
│  └──────────────┴──────────┴─────────┘      │
│                                             │
│  Model Usage:                               │
│  Sonnet: 3,420 tokens · Haiku: 1,205 tokens │
│  Estimated cost: $0.024                     │
│                                             │
╰─────────────────────────────────────────────╯
```

- Show each pipeline stage with a spinner while in progress, checkmark when done
- Display which model is being used for each stage
- Stream the final report section by section
- Show model usage and cost at the bottom

### 8. CLI (`cli.py`)

```bash
# Basic usage
sec-agent analyze AAPL
sec-agent analyze MSFT --filing-type 10-Q
sec-agent analyze TSLA --output json
sec-agent analyze NVDA --output markdown

# Options
--filing-type, -t     Specify filing type (10-K, 10-Q, 8-K). Default: latest available
--output, -o          Output format: terminal (default), json, markdown
--model, -m           Force a specific model for all stages
--verbose, -v         Show detailed pipeline logging
--no-cache            Skip any local caching
```

### 9. README.md

Write a comprehensive README with:
- Project title with a one-line description
- Badges: Python version, License, CI status
- "Quick Start" section (install + first command)
- Architecture diagram (ASCII, same as above)
- Feature list
- Detailed usage examples (CLI + Python API)
- Configuration section (env vars: ANTHROPIC_API_KEY, SEC_AGENT_MODEL, etc.)
- "How it works" section explaining the pipeline
- Contributing section
- License (MIT)

The README is critical — it's the first thing interviewers/recruiters see on GitHub.

---

## Implementation Order

1. **Phase 1: Foundation** — `pyproject.toml`, project structure, Pydantic models, config
2. **Phase 2: SEC Fetcher** — EDGAR API client with rate limiting and parsing
3. **Phase 3: Classifier + Router** — Filing type detection and routing logic
4. **Phase 4: LLM Layer** — Client abstraction, model router, prompt templates
5. **Phase 5: Analyzers** — 10-K, 10-Q, 8-K analyzers with structured output
6. **Phase 6: Terminal UI** — Rich-based streaming UI with pipeline progress
7. **Phase 7: CLI** — Typer CLI with all options
8. **Phase 8: Tests** — Unit tests with mocked LLM responses
9. **Phase 9: README + Polish** — Comprehensive README, examples, CI config

---

## Quality Requirements

- **Type hints everywhere** — use `mypy --strict` compatible types
- **All LLM outputs validated** with Pydantic — retry on validation failure
- **Async throughout** — fetcher and LLM calls are async
- **Error handling** — graceful failures with helpful error messages, never crash with a traceback
- **Rate limiting** — respect SEC EDGAR's 10 req/s limit
- **Cost tracking** — every LLM call tracked and reported
- **No hardcoded prompts** — all prompts in `prompts.py` as templates
- **Clean git history** — meaningful commits per phase

---

## Environment Variables

```bash
ANTHROPIC_API_KEY=sk-ant-...        # Required
OPENAI_API_KEY=sk-...               # Optional fallback
SEC_AGENT_MODEL=claude-sonnet-4-20250514   # Optional: force model
SEC_AGENT_USER_AGENT="SEC-Filing-Agent your@email.com"  # Required by SEC
```

---

## Definition of Done

The project is complete when:
- [ ] `sec-agent analyze AAPL` produces a correct, well-formatted terminal report
- [ ] `sec-agent analyze AAPL --output json` produces valid JSON matching AnalysisReport schema
- [ ] 10-K, 10-Q, and 8-K filings are all supported
- [ ] Model routing works (Sonnet for reasoning, Haiku for extraction)
- [ ] Terminal UI shows pipeline progress with per-stage model labels
- [ ] Cost/token tracking is displayed
- [ ] `pip install sec-filing-agent` works (proper pyproject.toml)
- [ ] Tests pass with mocked LLM responses
- [ ] README is comprehensive with architecture diagram and usage examples
- [ ] GitHub Actions CI runs lint + tests
