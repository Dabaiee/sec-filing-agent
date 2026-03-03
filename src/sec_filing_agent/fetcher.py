"""SEC EDGAR API client for fetching filings."""

from __future__ import annotations

import asyncio
import html
import re
import time
from datetime import date

import httpx

from sec_filing_agent.models.config import Settings
from sec_filing_agent.models.filing import RawFiling

# SEC EDGAR rate limit: max 10 requests/second
_rate_limit_interval = 0.1  # seconds between requests
_last_request_time = 0.0

COMPANY_TICKERS_URL = "https://www.sec.gov/files/company_tickers.json"
SUBMISSIONS_URL = "https://data.sec.gov/submissions/CIK{cik}.json"
ARCHIVES_BASE_URL = "https://www.sec.gov/Archives/edgar/data"


class FetcherError(Exception):
    """Error raised by the SEC EDGAR fetcher."""


async def _rate_limited_get(client: httpx.AsyncClient, url: str) -> httpx.Response:
    """Make a rate-limited GET request respecting SEC's 10 req/s limit."""
    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < _rate_limit_interval:
        await asyncio.sleep(_rate_limit_interval - elapsed)
    _last_request_time = time.monotonic()

    response = await client.get(url)
    if response.status_code == 429:
        await asyncio.sleep(1.0)
        response = await client.get(url)
    response.raise_for_status()
    return response


def _build_client(settings: Settings | None = None) -> httpx.AsyncClient:
    """Build an httpx AsyncClient with the required SEC headers."""
    if settings is None:
        settings = Settings.from_env()
    return httpx.AsyncClient(
        headers={
            "User-Agent": settings.sec_agent_user_agent,
            "Accept-Encoding": "gzip, deflate",
        },
        timeout=30.0,
        follow_redirects=True,
    )


async def lookup_cik(ticker: str, client: httpx.AsyncClient | None = None) -> tuple[str, str]:
    """Look up the CIK and company name for a ticker symbol.

    Returns:
        Tuple of (cik_zero_padded, company_name).

    Raises:
        FetcherError: If the ticker is not found.
    """
    own_client = client is None
    if own_client:
        client = _build_client()
    try:
        response = await _rate_limited_get(client, COMPANY_TICKERS_URL)
        data = response.json()
        ticker_upper = ticker.upper()
        for entry in data.values():
            if entry["ticker"].upper() == ticker_upper:
                cik = str(entry["cik_str"]).zfill(10)
                return cik, entry["title"]
        raise FetcherError(f"Ticker '{ticker}' not found in SEC EDGAR company tickers")
    finally:
        if own_client:
            await client.aclose()


async def fetch_filings_index(
    ticker: str, client: httpx.AsyncClient | None = None
) -> dict:
    """Fetch the filings index for a ticker from SEC EDGAR.

    Returns:
        The full submissions JSON response.
    """
    own_client = client is None
    if own_client:
        client = _build_client()
    try:
        cik, _company_name = await lookup_cik(ticker, client)
        url = SUBMISSIONS_URL.format(cik=cik)
        response = await _rate_limited_get(client, url)
        return response.json()
    finally:
        if own_client:
            await client.aclose()


def _strip_html(content: str) -> str:
    """Strip HTML tags and decode entities from filing content."""
    # Remove <style> and <script> blocks
    content = re.sub(r"<style[^>]*>.*?</style>", "", content, flags=re.DOTALL | re.IGNORECASE)
    content = re.sub(r"<script[^>]*>.*?</script>", "", content, flags=re.DOTALL | re.IGNORECASE)
    # Replace common block elements with newlines
    content = re.sub(r"<br\s*/?>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"</(p|div|tr|li|h[1-6])>", "\n", content, flags=re.IGNORECASE)
    content = re.sub(r"</td>", "\t", content, flags=re.IGNORECASE)
    # Strip all remaining tags
    content = re.sub(r"<[^>]+>", "", content)
    # Decode HTML entities
    content = html.unescape(content)
    # Collapse excessive whitespace
    content = re.sub(r"\n{3,}", "\n\n", content)
    content = re.sub(r"[ \t]{2,}", " ", content)
    return content.strip()


async def fetch_filing_content(
    cik: str, accession_number: str, primary_document: str, client: httpx.AsyncClient | None = None
) -> str:
    """Fetch and parse the raw text content of a filing document.

    Returns:
        Plain text content of the filing.
    """
    own_client = client is None
    if own_client:
        client = _build_client()
    try:
        # Accession number without dashes for the URL path
        accession_no_dashes = accession_number.replace("-", "")
        url = f"{ARCHIVES_BASE_URL}/{cik.lstrip('0')}/{accession_no_dashes}/{primary_document}"
        response = await _rate_limited_get(client, url)
        content = response.text
        # Strip HTML if the document is HTML
        if "<html" in content.lower() or "<body" in content.lower():
            content = _strip_html(content)
        # Truncate to ~100k chars to fit in LLM context
        max_chars = 100_000
        if len(content) > max_chars:
            content = content[:max_chars] + "\n\n[TRUNCATED — filing exceeds context limit]"
        return content
    finally:
        if own_client:
            await client.aclose()


async def fetch_latest_filing(
    ticker: str, filing_type: str | None = None, settings: Settings | None = None
) -> RawFiling:
    """Fetch the latest filing for a ticker, optionally filtered by type.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        filing_type: Optional filing type filter ("10-K", "10-Q", "8-K").
        settings: Optional settings override.

    Returns:
        RawFiling with the filing content.

    Raises:
        FetcherError: If no matching filing is found.
    """
    if settings is None:
        settings = Settings.from_env()
    async with _build_client(settings) as client:
        cik, company_name = await lookup_cik(ticker, client)
        url = SUBMISSIONS_URL.format(cik=cik)
        response = await _rate_limited_get(client, url)
        submissions = response.json()

        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        primary_documents = recent.get("primaryDocument", [])

        for i, form in enumerate(forms):
            if filing_type and form.upper() != filing_type.upper():
                continue
            if form.upper() in ("10-K", "10-Q", "8-K"):
                accession = accession_numbers[i]
                primary_doc = primary_documents[i]
                content = await fetch_filing_content(cik, accession, primary_doc, client)
                return RawFiling(
                    ticker=ticker.upper(),
                    cik=cik,
                    company_name=company_name,
                    accession_number=accession,
                    filing_type=form.upper(),
                    filing_date=date.fromisoformat(filing_dates[i]),
                    document_url=f"{ARCHIVES_BASE_URL}/{cik.lstrip('0')}/{accession.replace('-', '')}/{primary_doc}",
                    content=content,
                )

        type_msg = f" of type {filing_type}" if filing_type else ""
        raise FetcherError(f"No filing{type_msg} found for ticker '{ticker}'")


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
    if settings is None:
        settings = Settings.from_env()
    async with _build_client(settings) as client:
        cik, company_name = await lookup_cik(ticker, client)
        url = SUBMISSIONS_URL.format(cik=cik)
        response = await _rate_limited_get(client, url)
        submissions = response.json()

        recent = submissions.get("filings", {}).get("recent", {})
        forms = recent.get("form", [])
        accession_numbers = recent.get("accessionNumber", [])
        filing_dates = recent.get("filingDate", [])
        primary_documents = recent.get("primaryDocument", [])

        results: list[RawFiling] = []
        for i, form in enumerate(forms):
            if len(results) >= limit:
                break
            if filing_type and form.upper() != filing_type.upper():
                continue
            if form.upper() in ("10-K", "10-Q", "8-K"):
                accession = accession_numbers[i]
                primary_doc = primary_documents[i]
                content = await fetch_filing_content(cik, accession, primary_doc, client)
                results.append(
                    RawFiling(
                        ticker=ticker.upper(),
                        cik=cik,
                        company_name=company_name,
                        accession_number=accession,
                        filing_type=form.upper(),
                        filing_date=date.fromisoformat(filing_dates[i]),
                        document_url=f"{ARCHIVES_BASE_URL}/{cik.lstrip('0')}/{accession.replace('-', '')}/{primary_doc}",
                        content=content,
                    )
                )
        return results
