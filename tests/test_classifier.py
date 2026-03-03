"""Tests for filing classifier."""

from __future__ import annotations

from datetime import date

from sec_filing_agent.classifier import classify_filing
from sec_filing_agent.models.filing import RawFiling


def _make_filing(filing_type: str = "10-K", content: str = "") -> RawFiling:
    return RawFiling(
        ticker="AAPL",
        cik="0000320193",
        company_name="Apple Inc.",
        accession_number="0000320193-24-000123",
        filing_type=filing_type,
        filing_date=date(2024, 11, 1),
        document_url="https://example.com/filing.htm",
        content=content or f"FORM {filing_type}\nSample content",
    )


def test_classify_10k():
    filing = _make_filing("10-K")
    metadata = classify_filing(filing)
    assert metadata.filing_type == "10-K"
    assert metadata.company_name == "Apple Inc."
    assert metadata.ticker == "AAPL"


def test_classify_10q():
    filing = _make_filing("10-Q")
    metadata = classify_filing(filing)
    assert metadata.filing_type == "10-Q"


def test_classify_8k():
    filing = _make_filing("8-K")
    metadata = classify_filing(filing)
    assert metadata.filing_type == "8-K"


def test_classify_extracts_period_from_content():
    content = "FORM 10-K\nPERIOD OF REPORT: 2024-09-28\nContent here"
    filing = _make_filing("10-K", content=content)
    metadata = classify_filing(filing)
    assert "2024-09-28" in metadata.period_of_report


def test_classify_fallback_period_to_filing_date():
    filing = _make_filing("10-K", content="No period mentioned here")
    metadata = classify_filing(filing)
    assert metadata.period_of_report == "2024-11-01"


def test_classify_detects_type_from_content():
    filing = _make_filing("UNKNOWN", content="FORM 10-Q\nQuarterly Report")
    metadata = classify_filing(filing)
    assert metadata.filing_type == "10-Q"


def test_classify_annual_report_keyword():
    filing = _make_filing("UNKNOWN", content="ANNUAL REPORT pursuant to section 13")
    metadata = classify_filing(filing)
    assert metadata.filing_type == "10-K"
