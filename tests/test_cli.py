"""Tests for CLI and output formatting."""

from __future__ import annotations

from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.ui.terminal import render_json, render_markdown


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
