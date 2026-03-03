"""Tests for SEC EDGAR fetcher."""

from __future__ import annotations

import pytest
import httpx
import respx

from sec_filing_agent.fetcher import (
    FetcherError,
    _strip_html,
    lookup_cik,
)


MOCK_TICKERS_JSON = {
    "0": {"cik_str": 320193, "ticker": "AAPL", "title": "Apple Inc."},
    "1": {"cik_str": 789019, "ticker": "MSFT", "title": "MICROSOFT CORP"},
}

MOCK_SUBMISSIONS_JSON = {
    "cik": "0000320193",
    "entityType": "operating",
    "name": "Apple Inc.",
    "filings": {
        "recent": {
            "accessionNumber": ["0000320193-24-000123"],
            "filingDate": ["2024-11-01"],
            "form": ["10-K"],
            "primaryDocument": ["aapl-20240928.htm"],
        }
    },
}


@respx.mock
@pytest.mark.asyncio
async def test_lookup_cik_found():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MOCK_TICKERS_JSON)
    )
    async with httpx.AsyncClient() as client:
        cik, name = await lookup_cik("AAPL", client)
    assert cik == "0000320193"
    assert name == "Apple Inc."


@respx.mock
@pytest.mark.asyncio
async def test_lookup_cik_case_insensitive():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MOCK_TICKERS_JSON)
    )
    async with httpx.AsyncClient() as client:
        cik, name = await lookup_cik("aapl", client)
    assert cik == "0000320193"


@respx.mock
@pytest.mark.asyncio
async def test_lookup_cik_not_found():
    respx.get("https://www.sec.gov/files/company_tickers.json").mock(
        return_value=httpx.Response(200, json=MOCK_TICKERS_JSON)
    )
    async with httpx.AsyncClient() as client:
        with pytest.raises(FetcherError, match="not found"):
            await lookup_cik("ZZZZ", client)


def test_strip_html_basic():
    html = "<html><body><p>Hello <b>World</b></p></body></html>"
    result = _strip_html(html)
    assert "Hello World" in result
    assert "<" not in result


def test_strip_html_removes_style_and_script():
    html = "<style>.foo { color: red; }</style><script>alert('x')</script><p>Content</p>"
    result = _strip_html(html)
    assert "Content" in result
    assert "foo" not in result
    assert "alert" not in result


def test_strip_html_entities():
    html = "<p>Revenue &amp; Profit &gt; $1B</p>"
    result = _strip_html(html)
    assert "Revenue & Profit > $1B" in result
