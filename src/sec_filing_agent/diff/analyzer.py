"""Diff and comparison analyzer using LLM."""

from __future__ import annotations

from sec_filing_agent.diff.models import (
    CompanyComparison,
    ComparisonReport,
    DiffReport,
    DiffSummary,
)
from sec_filing_agent.diff.prompts import COMPARE_PROMPT, DIFF_PROMPT
from sec_filing_agent.fetcher import fetch_filings, fetch_latest_filing
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.model_router import ModelRouter
from sec_filing_agent.models.config import Settings
from sec_filing_agent.models.filing import RawFiling


async def _find_filing_by_date_hint(
    ticker: str, filing_type: str, date_hint: str, settings: Settings
) -> RawFiling:
    """Fetch filings and find one matching a date hint (e.g., '2023' or '2023-10-K')."""
    filings = await fetch_filings(ticker, limit=10, filing_type=filing_type, settings=settings)
    if not filings:
        from sec_filing_agent.fetcher import FetcherError
        raise FetcherError(f"No {filing_type} filings found for {ticker}")

    # Try to match by year or partial date
    for f in filings:
        date_str = str(f.filing_date)
        if date_hint in date_str or date_str.startswith(date_hint):
            return f

    # If no match, return the closest one and warn
    return filings[0]


async def diff_filings(
    ticker: str,
    filing_type: str,
    from_hint: str,
    to_hint: str,
    settings: Settings | None = None,
) -> DiffReport:
    """Compare two filings from the same company across time.

    Args:
        ticker: Stock ticker symbol.
        filing_type: Filing type (10-K, 10-Q, 8-K).
        from_hint: Date hint for the earlier filing (e.g., "2023").
        to_hint: Date hint for the later filing (e.g., "2024").
        settings: Optional settings override.

    Returns:
        DiffReport with the comparison.
    """
    if settings is None:
        settings = Settings.from_env()

    from_filing = await _find_filing_by_date_hint(ticker, filing_type, from_hint, settings)
    to_filing = await _find_filing_by_date_hint(ticker, filing_type, to_hint, settings)

    # Truncate content for diff (use first 50k each to fit both in context)
    max_chars = 50_000
    from_content = from_filing.content[:max_chars]
    to_content = to_filing.content[:max_chars]

    prompt = DIFF_PROMPT.format(
        filing_type=filing_type,
        company_name=from_filing.company_name,
        ticker=ticker.upper(),
        from_date=str(from_filing.filing_date),
        to_date=str(to_filing.filing_date),
        from_content=from_content,
        to_content=to_content,
    )

    llm_client = LLMClient(settings=settings)
    diff_summary, usage = await llm_client.complete_structured(
        prompt=prompt,
        response_model=DiffSummary,
        task_name="filing_diff_analysis",
        stage_label="Filing diff analysis",
    )

    total_tokens = usage.input_tokens + usage.output_tokens
    cost = ModelRouter.estimate_cost(usage.model, usage.input_tokens, usage.output_tokens)

    return DiffReport(
        ticker=ticker.upper(),
        company_name=from_filing.company_name,
        filing_type=filing_type,
        from_date=str(from_filing.filing_date),
        to_date=str(to_filing.filing_date),
        diff=diff_summary,
        total_tokens=total_tokens,
        estimated_cost_usd=round(cost, 4),
    )


async def compare_companies(
    ticker_a: str,
    ticker_b: str,
    filing_type: str = "10-K",
    settings: Settings | None = None,
) -> ComparisonReport:
    """Compare the latest filings of two companies.

    Args:
        ticker_a: First company ticker.
        ticker_b: Second company ticker.
        filing_type: Filing type to compare.
        settings: Optional settings override.

    Returns:
        ComparisonReport with the comparison.
    """
    if settings is None:
        settings = Settings.from_env()

    filing_a = await fetch_latest_filing(ticker_a, filing_type=filing_type, settings=settings)
    filing_b = await fetch_latest_filing(ticker_b, filing_type=filing_type, settings=settings)

    max_chars = 50_000
    content_a = filing_a.content[:max_chars]
    content_b = filing_b.content[:max_chars]

    prompt = COMPARE_PROMPT.format(
        filing_type=filing_type,
        company_a=filing_a.company_name,
        ticker_a=ticker_a.upper(),
        date_a=str(filing_a.filing_date),
        content_a=content_a,
        company_b=filing_b.company_name,
        ticker_b=ticker_b.upper(),
        date_b=str(filing_b.filing_date),
        content_b=content_b,
    )

    llm_client = LLMClient(settings=settings)
    comparison, usage = await llm_client.complete_structured(
        prompt=prompt,
        response_model=CompanyComparison,
        task_name="company_comparison_analysis",
        stage_label="Company comparison analysis",
    )

    total_tokens = usage.input_tokens + usage.output_tokens
    cost = ModelRouter.estimate_cost(usage.model, usage.input_tokens, usage.output_tokens)

    return ComparisonReport(
        ticker_a=ticker_a.upper(),
        ticker_b=ticker_b.upper(),
        company_a=filing_a.company_name,
        company_b=filing_b.company_name,
        filing_type=filing_type,
        comparison=comparison,
        total_tokens=total_tokens,
        estimated_cost_usd=round(cost, 4),
    )
