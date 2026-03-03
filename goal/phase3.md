# SEC Filing Intelligence Agent — Phase 3: edgartools Integration + Competitive Moat

Phase 1 built the core CLI. Phase 2 added product features. Phase 3 replaces the custom SEC fetcher/parser with `edgartools` (the dominant SEC data library) and deepens competitive differentiation.

IMPORTANT: Read the existing codebase first. Understand the current architecture before making changes. Do not break existing functionality. All existing tests must still pass after refactoring.

---

## Why This Phase

1. `edgartools` is the best SEC data library (typed Python objects, XBRL, financial statements, 1000+ tests). Building our own fetcher is reinventing a worse wheel.
2. By using edgartools as a dependency, we get: more filing types, XBRL financial data, better parsing, and community trust.
3. Our value is the **AI analysis layer**, not the data fetching. This phase sharpens that focus.

---

## Phase 3 Implementation Order

### 3.1: Replace Custom Fetcher with edgartools

**Add dependency:**
```
# pyproject.toml
dependencies = [
    ...
    "edgartools>=3.0.0",
]
```

**Refactor `fetcher.py`:**

Replace all custom SEC EDGAR HTTP calls with edgartools API:

```python
from edgar import Company, set_identity

# Must set identity per SEC policy
set_identity("SEC-Filing-Agent your@email.com")

class EdgarFetcher:
    """Fetches SEC filings using edgartools library."""

    async def fetch_latest_filing(self, ticker: str, filing_type: str | None = None) -> RawFiling:
        company = Company(ticker)

        if filing_type:
            filings = company.get_filings(form=filing_type)
        else:
            # Get latest of any supported type
            filings = company.get_filings(form=["10-K", "10-Q", "8-K"])

        if not filings or len(filings) == 0:
            raise FilingNotFoundError(f"No filings found for {ticker}")

        latest = filings[0]
        filing_obj = latest.obj()

        return RawFiling(
            ticker=ticker,
            company_name=company.name,
            cik=str(company.cik),
            filing_type=latest.form,
            filing_date=str(latest.filing_date),
            accession_number=latest.accession_no,
            text_content=latest.text() if hasattr(latest, 'text') else str(filing_obj),
            filing_obj=filing_obj,  # Keep the typed object for structured extraction
            raw_filing=latest,      # Keep original edgartools filing object
        )

    async def fetch_filings(self, ticker: str, filing_type: str | None = None, limit: int = 5) -> list[RawFiling]:
        company = Company(ticker)
        if filing_type:
            filings = company.get_filings(form=filing_type).head(limit)
        else:
            filings = company.get_filings(form=["10-K", "10-Q", "8-K"]).head(limit)
        return [self._to_raw_filing(ticker, company, f) for f in filings]

    async def get_financials(self, ticker: str) -> dict:
        """Get structured XBRL financial data — edgartools exclusive feature."""
        company = Company(ticker)
        financials = company.get_financials()
        return {
            "income_statement": financials.income_statement(),
            "balance_sheet": financials.balance_sheet(),
            "cash_flow": financials.cash_flow_statement(),
        }

    async def get_facts(self, ticker: str, concept: str) -> "pd.DataFrame":
        """Get historical financial facts (e.g., revenue over time)."""
        company = Company(ticker)
        facts = company.get_facts()
        return facts.to_pandas(concept)
```

**Update `models/filing.py`:**
```python
from typing import Any

class RawFiling(BaseModel):
    ticker: str
    company_name: str
    cik: str
    filing_type: str
    filing_date: str
    accession_number: str
    text_content: str
    filing_obj: Any = None   # edgartools typed object (10-K, 10-Q, 8-K obj)
    raw_filing: Any = None   # original edgartools Filing object

    class Config:
        arbitrary_types_allowed = True
```

**Delete:** Any custom HTTP code for SEC EDGAR, rate limiting logic (edgartools handles this), HTML parsing code.

**Keep:** The `RawFiling` model as an abstraction layer so the rest of the pipeline doesn't depend directly on edgartools.

Commit: "refactor: replace custom SEC fetcher with edgartools library"

---

### 3.2: Enhance Analyzers with Structured Financial Data

Now that edgartools gives us XBRL financial statements as DataFrames, our analyzers can provide **actual numbers** instead of relying on LLM extraction from raw text.

**Refactor analyzers to use hybrid approach:**

```python
class TenKAnalyzer(BaseAnalyzer):
    async def analyze(self, filing: RawFiling, metadata: FilingMetadata) -> AnalysisReport:
        # STEP 1: Extract STRUCTURED financial data from edgartools (no LLM needed)
        financials = await self.fetcher.get_financials(filing.ticker)
        financial_highlights = self._extract_financial_highlights(financials)

        # STEP 2: Use LLM ONLY for unstructured analysis (risk factors, MD&A, forward-looking)
        risk_factors = await self._analyze_risk_factors(filing.text_content)  # LLM: Sonnet
        management_discussion = await self._analyze_mda(filing.text_content)  # LLM: Sonnet
        forward_looking = await self._extract_forward_looking(filing.text_content)  # LLM: Haiku

        # STEP 3: Generate executive summary combining structured + unstructured
        summary = await self._generate_summary(financial_highlights, risk_factors)  # LLM: Sonnet

        return AnalysisReport(
            ticker=filing.ticker,
            company_name=filing.company_name,
            filing_type="10-K",
            filing_date=filing.filing_date,
            financial_highlights=financial_highlights,  # REAL numbers from XBRL
            risk_factors=risk_factors,                   # LLM analysis
            management_discussion=management_discussion, # LLM analysis
            forward_looking=forward_looking,             # LLM extraction
            summary=summary,
            ...
        )

    def _extract_financial_highlights(self, financials: dict) -> FinancialHighlights:
        """Extract REAL financial numbers from XBRL — no LLM hallucination possible."""
        income = financials["income_statement"]
        # Extract actual values from DataFrame
        return FinancialHighlights(
            revenue=self._format_currency(income, "Revenue"),
            net_income=self._format_currency(income, "NetIncome"),
            gross_margin=self._calc_margin(income, "GrossProfit", "Revenue"),
            operating_margin=self._calc_margin(income, "OperatingIncome", "Revenue"),
            yoy_revenue_change=self._calc_yoy(income, "Revenue"),
            key_metrics={...},
        )
```

**Key insight: This is a MASSIVE competitive advantage.**

Every other SEC+LLM tool uses LLM to extract financial numbers from text → hallucination risk.
We use XBRL structured data for numbers → 100% accurate. LLM is only used for qualitative analysis (risk factors, MD&A) where it excels.

**Update terminal UI to show this:**
```
  ✓ Financial data extracted from XBRL          [structured — no LLM]
  ✓ Risk factors analyzed                        [claude-sonnet]
  ✓ Management discussion analyzed               [claude-sonnet]
  ✓ Forward-looking statements extracted          [claude-haiku]
```

This signals: "we know when to use LLM and when NOT to." Production AI engineering.

Commit: "feat: hybrid analysis — XBRL structured data + LLM qualitative analysis"

---

### 3.3: Add Financial Trend Analysis

edgartools gives us historical XBRL facts. Use this for multi-year trend analysis.

**New CLI command:**
```bash
sec-agent trends AAPL --years 5
```

**Output:**
```
╭─ AAPL — 5-Year Financial Trends ──────────────────╮
│                                                     │
│  Revenue ($B)                                       │
│  2020: $274.5  ████████████████████                 │
│  2021: $365.8  ██████████████████████████           │
│  2022: $394.3  ████████████████████████████         │
│  2023: $383.3  ███████████████████████████          │
│  2024: $394.3  ████████████████████████████         │
│                                                     │
│  Net Margin                                         │
│  2020: 20.9%   ████████████                         │
│  2021: 25.9%   ███████████████                      │
│  2022: 25.3%   ██████████████                       │
│  2023: 25.3%   ██████████████                       │
│  2024: 23.8%   █████████████                        │
│                                                     │
│  AI Analysis:                                       │
│  Revenue recovered to 2022 highs after 2023 dip.    │
│  Margin compression in 2024 driven by increased     │
│  R&D spending on AI initiatives (+18% YoY).         │
│                                                     │
╰─────────────────────────────────────────────────────╯
```

**Implementation:**
```python
# In fetcher.py — already have get_facts()
revenue_history = await fetcher.get_facts("AAPL", "us-gaap:Revenues")

# In new file: src/sec_filing_agent/trends.py
class TrendAnalyzer:
    async def analyze_trends(self, ticker: str, years: int = 5) -> TrendReport:
        # 1. Fetch multi-year XBRL data (structured, no LLM)
        facts = await self.fetcher.get_facts(ticker, concepts=[
            "us-gaap:Revenues",
            "us-gaap:NetIncomeLoss",
            "us-gaap:GrossProfit",
            "us-gaap:OperatingIncomeLoss",
            "us-gaap:EarningsPerShareDiluted",
        ])

        # 2. Compute trends, growth rates, margins (pure math, no LLM)
        trend_data = self._compute_trends(facts, years)

        # 3. LLM generates narrative summary of the trends (Haiku — simple task)
        narrative = await self._generate_narrative(trend_data)

        return TrendReport(
            ticker=ticker,
            years=years,
            metrics=trend_data,
            narrative=narrative,
            model_usage=...,
        )
```

**New Pydantic models in `models/trends.py`:**
```python
class TrendReport(BaseModel):
    ticker: str
    company_name: str
    years: int
    metrics: list[MetricTrend]
    narrative: str  # LLM-generated summary
    model_usage: ModelUsage

class MetricTrend(BaseModel):
    name: str  # "Revenue", "Net Income", etc.
    unit: str  # "$B", "%", "$/share"
    data_points: list[YearValue]
    cagr: float | None  # Compound annual growth rate
    trend_direction: str  # "up", "down", "flat", "volatile"

class YearValue(BaseModel):
    year: int
    value: float
    formatted: str  # "$394.3B", "23.8%"
```

Commit: "feat: add multi-year financial trend analysis with XBRL data"

---

### 3.4: Sector Comparison

Compare a company against its sector peers.

**CLI:**
```bash
sec-agent sector AAPL
# Auto-detects sector (Technology), compares against top peers

sec-agent sector AAPL --peers MSFT GOOG META
# Compare against specific peers
```

**Implementation:**
- Use edgartools to fetch financials for target + peers
- Compute relative metrics (revenue growth, margins, P/E if available)
- LLM generates competitive positioning summary

```python
class SectorAnalyzer:
    # Default peer mapping (can be overridden)
    SECTOR_PEERS = {
        "Technology": ["AAPL", "MSFT", "GOOG", "META", "NVDA", "AMZN"],
        "Finance": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
        ...
    }

    async def compare_sector(self, ticker: str, peers: list[str] | None = None) -> SectorReport:
        if peers is None:
            peers = self._get_default_peers(ticker)

        # Fetch financials for all companies (parallel)
        all_financials = await asyncio.gather(*[
            self.fetcher.get_financials(t) for t in [ticker] + peers
        ])

        # Compute relative metrics (pure math)
        comparison = self._compute_comparison(ticker, peers, all_financials)

        # LLM generates competitive positioning narrative
        narrative = await self._generate_positioning(comparison)

        return SectorReport(...)
```

Commit: "feat: add sector peer comparison analysis"

---

### 3.5: Update Streamlit App for New Features

If Phase 2 built the Streamlit app, add tabs for the new features:

```
Tabs: [Single Analysis] [Compare/Diff] [Trends] [Sector] [Watchlist]
```

- **Trends tab**: Ticker input → interactive charts (use Streamlit's built-in charts or plotly)
- **Sector tab**: Ticker input → peer comparison table + narrative

Commit: "feat: add trends and sector tabs to Streamlit app"

---

### 3.6: Update Tests

```
tests/
├── test_edgartools_fetcher.py   # Test edgartools integration (mocked)
├── test_hybrid_analyzer.py      # Test XBRL + LLM hybrid approach
├── test_trends.py               # Test trend analysis
├── test_sector.py               # Test sector comparison
```

Mock edgartools responses in tests — do not make real SEC API calls.

Commit: "test: add tests for Phase 3 features"

---

### 3.7: Update README

Add a "How It Works" section highlighting the hybrid approach:

```markdown
## How It Works

Unlike other SEC analysis tools that use LLM for everything (including financial number extraction),
sec-filing-agent uses a **hybrid approach**:

| Data Type | Source | Why |
|-----------|--------|-----|
| Financial numbers (revenue, margins, EPS) | XBRL structured data via edgartools | 100% accurate, no hallucination |
| Risk factors, MD&A, forward-looking | LLM analysis (Claude/GPT-4) | Qualitative reasoning is LLM's strength |
| Multi-year trends | XBRL historical facts | Real data, computed metrics |
| Executive summary | LLM synthesis | Combines structured + qualitative |

This means financial numbers in our reports are **never hallucinated** — they come directly from
SEC XBRL filings. LLM is used only where it adds value: understanding, summarization, and reasoning.
```

Add comparison table vs competitors:

```markdown
## Comparison

| Feature | sec-filing-agent | sec-insights | 10K-Analyzer | sec-edgar-agentkit |
|---------|-----------------|--------------|--------------|-------------------|
| CLI tool | ✅ | ❌ | ❌ | ❌ |
| Structured JSON output | ✅ | ❌ | ❌ | ❌ |
| XBRL financial data | ✅ | ❌ | ❌ | ✅ |
| Hallucination-free numbers | ✅ | ❌ | ❌ | ❌ |
| Model routing (cost optimization) | ✅ | ❌ | ❌ | ❌ |
| Multi-filing type (10-K/10-Q/8-K) | ✅ | ✅ | 10-K only | ✅ |
| Trend analysis | ✅ | ❌ | ❌ | ❌ |
| Sector comparison | ✅ | ❌ | ❌ | ❌ |
| pip install | ✅ | ❌ | ❌ | ✅ |
| Local model support (Ollama) | ✅ | ❌ | ❌ | ❌ |
```

Commit: "docs: update README with hybrid approach and competitor comparison"

---

## Quality Requirements

- All Phase 1 and Phase 2 tests must still pass
- New features must have tests with mocked edgartools + LLM responses
- `ruff check` and `mypy` must pass
- pyproject.toml version bumped to 0.3.0

## Definition of Done

- [ ] Custom SEC fetcher replaced with edgartools — all existing features still work
- [ ] Analyzers use hybrid approach: XBRL for numbers, LLM for qualitative analysis
- [ ] `sec-agent trends AAPL --years 5` shows multi-year financial trends with ASCII charts
- [ ] `sec-agent sector AAPL` shows peer comparison
- [ ] Terminal UI shows "[structured — no LLM]" vs "[claude-sonnet]" per stage
- [ ] README has "How It Works" hybrid explanation and competitor comparison table
- [ ] All tests pass (Phase 1 + Phase 2 + Phase 3)
- [ ] pyproject.toml version is 0.3.0
