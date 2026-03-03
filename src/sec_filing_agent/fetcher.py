"""SEC EDGAR data fetcher using edgartools library.

Includes a simple TTL cache for Company lookups and financial data
to avoid redundant SEC API calls during batch operations.
"""

from __future__ import annotations

import logging
import time
from datetime import date
from typing import Any

from edgar import Company, set_identity

from sec_filing_agent.models.config import Settings
from sec_filing_agent.models.filing import RawFiling

logger = logging.getLogger(__name__)

SUPPORTED_FORMS = ("10-K", "10-Q", "8-K")

# ── TTL Cache ────────────────────────────────────────────────────────────────

# Default cache TTL: 5 minutes (SEC filings don't change frequently)
_CACHE_TTL_S = 300

_company_cache: dict[str, tuple[Company, float]] = {}
_financials_cache: dict[str, tuple[dict[str, Any] | None, float]] = {}


def _cache_get(cache: dict[str, tuple[Any, float]], key: str) -> Any | None:
    """Get a value from a TTL cache, returning None if expired or missing."""
    entry = cache.get(key)
    if entry is None:
        return None
    value, ts = entry
    if time.monotonic() - ts > _CACHE_TTL_S:
        del cache[key]
        return None
    return value


def _cache_set(cache: dict[str, tuple[Any, float]], key: str, value: Any) -> None:
    """Store a value in a TTL cache."""
    cache[key] = (value, time.monotonic())


def clear_cache() -> None:
    """Clear all cached data. Useful for testing or long-running processes."""
    _company_cache.clear()
    _financials_cache.clear()


class FetcherError(Exception):
    """Error raised by the SEC EDGAR fetcher."""


def _init_identity(settings: Settings | None = None) -> None:
    """Set SEC EDGAR identity per SEC policy."""
    if settings is None:
        settings = Settings.from_env()
    set_identity(settings.sec_agent_user_agent)


def _filing_to_raw(ticker: str, company: Company, filing: Any) -> RawFiling:
    """Convert an edgartools Filing object to our RawFiling model."""
    # Get text content from the filing
    try:
        text_content = filing.text()
    except Exception:
        text_content = str(filing)

    # Truncate to fit LLM context
    max_chars = 100_000
    if len(text_content) > max_chars:
        text_content = text_content[:max_chars] + "\n\n[TRUNCATED — filing exceeds context limit]"

    filing_date_val = filing.filing_date
    if isinstance(filing_date_val, str):
        filing_date_val = date.fromisoformat(filing_date_val)

    return RawFiling(
        ticker=ticker.upper(),
        cik=str(company.cik),
        company_name=company.name,
        accession_number=filing.accession_no,
        filing_type=filing.form.upper(),
        filing_date=filing_date_val,
        document_url=f"https://www.sec.gov/Archives/edgar/data/{company.cik}/{filing.accession_no}",
        content=text_content,
        filing_obj=filing,
    )


async def fetch_latest_filing(
    ticker: str, filing_type: str | None = None, settings: Settings | None = None
) -> RawFiling:
    """Fetch the latest filing for a ticker using edgartools.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        filing_type: Optional filing type filter ("10-K", "10-Q", "8-K").
        settings: Optional settings override.

    Returns:
        RawFiling with the filing content.

    Raises:
        FetcherError: If no matching filing is found.
    """
    _init_identity(settings)

    try:
        company = Company(ticker)
    except Exception as e:
        raise FetcherError(f"Company not found for ticker '{ticker}': {e}") from e

    if filing_type:
        filings = company.get_filings(form=filing_type)
    else:
        filings = company.get_filings(form=list(SUPPORTED_FORMS))

    if not filings or len(filings) == 0:
        type_msg = f" of type {filing_type}" if filing_type else ""
        raise FetcherError(f"No filing{type_msg} found for ticker '{ticker}'")

    latest = filings[0]
    return _filing_to_raw(ticker, company, latest)


async def fetch_filings(
    ticker: str, limit: int = 5, filing_type: str | None = None, settings: Settings | None = None
) -> list[RawFiling]:
    """Fetch multiple filings for a ticker.

    Args:
        ticker: Stock ticker symbol.
        limit: Maximum number of filings to return.
        filing_type: Optional filing type filter.
        settings: Optional settings override.

    Returns:
        List of RawFiling objects.
    """
    _init_identity(settings)

    try:
        company = Company(ticker)
    except Exception as e:
        raise FetcherError(f"Company not found for ticker '{ticker}': {e}") from e

    if filing_type:
        filings = company.get_filings(form=filing_type)
    else:
        filings = company.get_filings(form=list(SUPPORTED_FORMS))

    results: list[RawFiling] = []
    for i, filing in enumerate(filings):
        if i >= limit:
            break
        try:
            results.append(_filing_to_raw(ticker, company, filing))
        except Exception as e:
            logger.warning("Failed to process filing %d for %s: %s", i, ticker, e)
            continue

    return results


async def get_company(ticker: str, settings: Settings | None = None) -> Company:
    """Get an edgartools Company object for a ticker.

    Uses a TTL cache to avoid redundant SEC API calls during batch operations.

    Args:
        ticker: Stock ticker symbol.
        settings: Optional settings override.

    Returns:
        edgartools Company object.
    """
    _init_identity(settings)
    key = ticker.upper()
    cached = _cache_get(_company_cache, key)
    if cached is not None:
        logger.debug("Cache hit for company '%s'", key)
        return cached
    try:
        company = Company(ticker)
    except Exception as e:
        raise FetcherError(f"Company not found for ticker '{ticker}': {e}") from e
    _cache_set(_company_cache, key, company)
    return company


async def get_financials(ticker: str, settings: Settings | None = None) -> dict[str, Any] | None:
    """Get structured XBRL financial statements for a ticker.

    Results are cached for the TTL duration to avoid redundant API calls.

    Args:
        ticker: Stock ticker symbol.
        settings: Optional settings override.

    Returns:
        Dict with income_statement, balance_sheet, cash_flow DataFrames, or None.
    """
    key = ticker.upper()
    cached: dict[str, Any] | None = _cache_get(_financials_cache, key)
    if cached is not None:
        logger.debug("Cache hit for financials '%s'", key)
        return cached
    company = await get_company(ticker, settings)
    financials = company.get_financials()
    if financials is None:
        _cache_set(_financials_cache, key, None)
        return None
    result: dict[str, Any] = {
        "income_statement": financials.income_statement,
        "balance_sheet": financials.balance_sheet,
        "cash_flow": financials.cash_flow_statement,
        "financials_obj": financials,
    }
    _cache_set(_financials_cache, key, result)
    return result


async def get_facts(ticker: str, settings: Settings | None = None) -> Any:
    """Get historical XBRL facts for a ticker.

    Args:
        ticker: Stock ticker symbol.
        settings: Optional settings override.

    Returns:
        edgartools EntityFacts object, or None.
    """
    company = await get_company(ticker, settings)
    return company.get_facts()
