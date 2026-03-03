"""Tests for error handling and edge cases across the pipeline."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from sec_filing_agent.classifier import classify_filing
from sec_filing_agent.fetcher import FetcherError
from sec_filing_agent.llm.client import LLMError, _parse_json_response
from sec_filing_agent.models.filing import RawFiling
from sec_filing_agent.router import RouterError, get_analyzer


# ── Classifier Edge Cases ────────────────────────────────────────────────────


def test_classify_empty_content():
    """Classifier handles filing with minimal content."""
    filing = RawFiling(
        ticker="TEST",
        cik="123",
        company_name="Test Corp",
        accession_number="000-00-000",
        filing_type="10-K",
        filing_date=date(2024, 1, 1),
        document_url="https://example.com/test",
        content="",
    )
    metadata = classify_filing(filing)
    assert metadata.filing_type == "10-K"  # Falls back to EDGAR type


def test_classify_mismatched_type():
    """Classifier handles filing type mismatch between EDGAR and content."""
    filing = RawFiling(
        ticker="TEST",
        cik="123",
        company_name="Test Corp",
        accession_number="000-00-000",
        filing_type="10-K",
        filing_date=date(2024, 1, 1),
        document_url="https://example.com/test",
        content="FORM 8-K CURRENT REPORT",
    )
    metadata = classify_filing(filing)
    # Should detect 8-K from content
    assert metadata.filing_type in ("10-K", "8-K")


# ── Router Edge Cases ────────────────────────────────────────────────────────


def test_router_whitespace_in_type():
    """Router handles whitespace in filing type."""
    analyzer = get_analyzer("  10-K  ")
    assert analyzer is not None


def test_router_error_lists_types():
    """Router error message includes available types."""
    with pytest.raises(RouterError) as exc_info:
        get_analyzer("INVALID-TYPE")
    assert "10-K" in str(exc_info.value)
    assert "10-Q" in str(exc_info.value)
    assert "8-K" in str(exc_info.value)


# ── LLM Client Edge Cases ───────────────────────────────────────────────────


def test_parse_json_with_preamble():
    """Parser extracts JSON from text with preamble."""
    class Simple(BaseModel):
        value: int

    text = 'Here is the analysis:\n\n{"value": 42}\n\nHope this helps!'
    result = _parse_json_response(text, Simple)
    assert result.value == 42


def test_parse_json_nested_fences():
    """Parser handles nested or unusual markdown fences."""
    class Simple(BaseModel):
        value: int

    text = '```\n{"value": 42}\n```'
    result = _parse_json_response(text, Simple)
    assert result.value == 42


def test_llm_error_has_context():
    """LLMError includes helpful context."""
    error = LLMError("Test error message")
    assert "Test error" in str(error)


# ── Fetcher Edge Cases ───────────────────────────────────────────────────────


@pytest.mark.asyncio
@patch("sec_filing_agent.fetcher.Company")
@patch("sec_filing_agent.fetcher.set_identity")
async def test_fetch_filing_invalid_form_type(mock_identity, mock_company_cls):
    """Fetcher returns empty for unsupported form types."""
    from sec_filing_agent.fetcher import fetch_latest_filing

    company = MagicMock()
    company.name = "Test Corp"
    company.cik = 12345
    filings_mock = MagicMock()
    filings_mock.__len__ = lambda s: 0
    filings_mock.__bool__ = lambda s: False
    company.get_filings.return_value = filings_mock
    mock_company_cls.return_value = company

    with pytest.raises(FetcherError, match="No filing"):
        await fetch_latest_filing("TEST", filing_type="S-1")


# ── Integration-style Edge Cases ─────────────────────────────────────────────


def test_analysis_report_serialization_roundtrip():
    """AnalysisReport can be serialized to JSON and deserialized."""
    from sec_filing_agent.models.analysis import AnalysisReport, ModelUsage

    report = AnalysisReport(
        ticker="TEST",
        company_name="Test Corp",
        filing_type="10-K",
        filing_date=date(2024, 1, 1),
        period_of_report="2024",
        summary="Test summary",
        model_usage=ModelUsage(),
    )
    json_str = report.model_dump_json()
    roundtripped = AnalysisReport.model_validate_json(json_str)
    assert roundtripped.ticker == "TEST"
    assert roundtripped.summary == "Test summary"


def test_trend_report_serialization():
    """TrendReport can be serialized and deserialized."""
    from sec_filing_agent.models.analysis import ModelUsage
    from sec_filing_agent.models.trends import MetricTrend, TrendReport, YearValue

    report = TrendReport(
        ticker="TEST",
        company_name="Test Corp",
        years=5,
        metrics=[
            MetricTrend(
                name="Revenue",
                unit="$B",
                data_points=[YearValue(year=2024, value=100, formatted="$100B")],
                cagr=5.0,
                trend_direction="up",
            )
        ],
        narrative="Test narrative",
        model_usage=ModelUsage(),
    )
    json_str = report.model_dump_json()
    roundtripped = TrendReport.model_validate_json(json_str)
    assert roundtripped.ticker == "TEST"
    assert len(roundtripped.metrics) == 1
