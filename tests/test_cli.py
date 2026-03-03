"""Tests for CLI and output formatting."""

from __future__ import annotations

import click.exceptions
import pytest

from sec_filing_agent.cli import _validate_filing_type, _validate_ticker
from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.ui.terminal import render_json, render_markdown


# ── Output Rendering ────────────────────────────────────────────────────────


def test_render_json(sample_report: AnalysisReport):
    output = render_json(sample_report)
    assert '"ticker": "AAPL"' in output
    assert '"revenue": "$394.3B"' in output
    # Verify it's valid JSON
    import json
    data = json.loads(output)
    assert data["ticker"] == "AAPL"
    assert data["filing_type"] == "10-K"


def test_render_markdown(sample_report: AnalysisReport):
    output = render_markdown(sample_report)
    assert "# AAPL" in output
    assert "Apple Inc." in output
    assert "## Summary" in output
    assert "## Risk Factors" in output
    assert "## Financial Highlights" in output
    assert "$394.3B" in output


def test_render_json_validates_schema(sample_report: AnalysisReport):
    """Ensure JSON output can be round-tripped through the model."""
    output = render_json(sample_report)
    reimported = AnalysisReport.model_validate_json(output)
    assert reimported.ticker == "AAPL"
    assert reimported.financial_highlights is not None
    assert reimported.financial_highlights.revenue == "$394.3B"


# ── Input Validation ────────────────────────────────────────────────────────


def test_validate_ticker_normal():
    """Valid ticker is uppercased."""
    assert _validate_ticker("aapl") == "AAPL"


def test_validate_ticker_with_whitespace():
    """Whitespace is stripped."""
    assert _validate_ticker("  msft  ") == "MSFT"


def test_validate_ticker_rejects_numbers():
    """Ticker with digits is rejected."""
    with pytest.raises(click.exceptions.Exit):
        _validate_ticker("A1B2")


def test_validate_ticker_rejects_long():
    """Ticker longer than 5 characters is rejected."""
    with pytest.raises(click.exceptions.Exit):
        _validate_ticker("TOOLONG")


def test_validate_ticker_rejects_empty():
    """Empty ticker is rejected."""
    with pytest.raises(click.exceptions.Exit):
        _validate_ticker("")


def test_validate_filing_type_valid():
    """Valid filing types are normalized to uppercase."""
    assert _validate_filing_type("10-k") == "10-K"
    assert _validate_filing_type("10-Q") == "10-Q"
    assert _validate_filing_type("8-K") == "8-K"


def test_validate_filing_type_none():
    """None filing type passes through."""
    assert _validate_filing_type(None) is None


def test_validate_filing_type_invalid():
    """Invalid filing type is rejected."""
    with pytest.raises(click.exceptions.Exit):
        _validate_filing_type("S-1")
