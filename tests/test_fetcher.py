"""Tests for SEC EDGAR fetcher (edgartools-based)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest

from sec_filing_agent.fetcher import (
    FetcherError,
    _filing_to_raw,
    fetch_latest_filing,
)


def _make_mock_company(ticker: str = "AAPL", name: str = "Apple Inc.", cik: int = 320193):
    """Create a mock edgartools Company object."""
    company = MagicMock()
    company.name = name
    company.cik = cik
    company.tickers = [ticker]
    return company


def _make_mock_filing(
    form: str = "10-K",
    filing_date: str = "2024-11-01",
    accession_no: str = "0000320193-24-000123",
    text: str = "FORM 10-K ANNUAL REPORT...",
):
    """Create a mock edgartools Filing object."""
    filing = MagicMock()
    filing.form = form
    filing.filing_date = filing_date
    filing.accession_no = accession_no
    filing.text.return_value = text
    return filing


def test_filing_to_raw_basic():
    """Test converting edgartools filing to RawFiling."""
    company = _make_mock_company()
    filing = _make_mock_filing()
    raw = _filing_to_raw("AAPL", company, filing)

    assert raw.ticker == "AAPL"
    assert raw.company_name == "Apple Inc."
    assert raw.cik == "320193"
    assert raw.filing_type == "10-K"
    assert raw.filing_date == date(2024, 11, 1)
    assert raw.accession_number == "0000320193-24-000123"
    assert "FORM 10-K" in raw.content
    assert raw.filing_obj is filing


def test_filing_to_raw_truncates_long_content():
    """Test that very long filing content is truncated."""
    company = _make_mock_company()
    long_text = "x" * 200_000
    filing = _make_mock_filing(text=long_text)
    raw = _filing_to_raw("AAPL", company, filing)

    assert len(raw.content) < 200_000
    assert "[TRUNCATED" in raw.content


def test_filing_to_raw_case_insensitive_ticker():
    """Test that ticker is uppercased."""
    company = _make_mock_company()
    filing = _make_mock_filing()
    raw = _filing_to_raw("aapl", company, filing)
    assert raw.ticker == "AAPL"


@pytest.mark.asyncio
@patch("sec_filing_agent.fetcher.Company")
@patch("sec_filing_agent.fetcher.set_identity")
async def test_fetch_latest_filing_found(mock_identity, mock_company_cls):
    """Test fetching the latest filing successfully."""
    company = _make_mock_company()
    filing = _make_mock_filing()
    filings_mock = MagicMock()
    filings_mock.__len__ = lambda s: 1
    filings_mock.__bool__ = lambda s: True
    filings_mock.__getitem__ = lambda s, i: filing
    company.get_filings.return_value = filings_mock
    mock_company_cls.return_value = company

    raw = await fetch_latest_filing("AAPL", filing_type="10-K")
    assert raw.ticker == "AAPL"
    assert raw.filing_type == "10-K"


@pytest.mark.asyncio
@patch("sec_filing_agent.fetcher.Company")
@patch("sec_filing_agent.fetcher.set_identity")
async def test_fetch_latest_filing_not_found(mock_identity, mock_company_cls):
    """Test error when no filings are found."""
    company = _make_mock_company()
    filings_mock = MagicMock()
    filings_mock.__len__ = lambda s: 0
    filings_mock.__bool__ = lambda s: False
    company.get_filings.return_value = filings_mock
    mock_company_cls.return_value = company

    with pytest.raises(FetcherError, match="No filing"):
        await fetch_latest_filing("AAPL", filing_type="10-K")


@pytest.mark.asyncio
@patch("sec_filing_agent.fetcher.Company")
@patch("sec_filing_agent.fetcher.set_identity")
async def test_fetch_latest_filing_company_not_found(mock_identity, mock_company_cls):
    """Test error when company ticker is invalid."""
    mock_company_cls.side_effect = Exception("Company not found")

    with pytest.raises(FetcherError, match="Company not found"):
        await fetch_latest_filing("ZZZZ")
