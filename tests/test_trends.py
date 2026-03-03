"""Tests for multi-year financial trend analysis."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sec_filing_agent.models.trends import MetricTrend, YearValue
from sec_filing_agent.trends import _calc_cagr, _calc_direction, _format_trends_for_prompt


def test_calc_cagr_basic():
    """Test basic CAGR calculation."""
    data = [
        YearValue(year=2020, value=100, formatted="$100"),
        YearValue(year=2024, value=200, formatted="$200"),
    ]
    cagr = _calc_cagr(data)
    assert cagr is not None
    assert abs(cagr - 18.92) < 0.1  # ~18.92% CAGR for doubling in 4 years


def test_calc_cagr_single_point():
    """CAGR with single data point returns None."""
    data = [YearValue(year=2024, value=100, formatted="$100")]
    assert _calc_cagr(data) is None


def test_calc_cagr_zero_start():
    """CAGR with zero start value returns None."""
    data = [
        YearValue(year=2020, value=0, formatted="$0"),
        YearValue(year=2024, value=100, formatted="$100"),
    ]
    assert _calc_cagr(data) is None


def test_calc_direction_up():
    """Test upward trend detection."""
    data = [
        YearValue(year=2020, value=100, formatted="$100"),
        YearValue(year=2021, value=120, formatted="$120"),
        YearValue(year=2022, value=140, formatted="$140"),
        YearValue(year=2023, value=160, formatted="$160"),
    ]
    assert _calc_direction(data) == "up"


def test_calc_direction_down():
    """Test downward trend detection."""
    data = [
        YearValue(year=2020, value=160, formatted="$160"),
        YearValue(year=2021, value=140, formatted="$140"),
        YearValue(year=2022, value=120, formatted="$120"),
        YearValue(year=2023, value=100, formatted="$100"),
    ]
    assert _calc_direction(data) == "down"


def test_calc_direction_volatile():
    """Test volatile trend detection."""
    data = [
        YearValue(year=2020, value=100, formatted="$100"),
        YearValue(year=2021, value=150, formatted="$150"),
        YearValue(year=2022, value=90, formatted="$90"),
        YearValue(year=2023, value=130, formatted="$130"),
        YearValue(year=2024, value=80, formatted="$80"),
    ]
    assert _calc_direction(data) == "volatile"


def test_calc_direction_flat():
    """Test flat trend detection (single point)."""
    data = [YearValue(year=2020, value=100, formatted="$100")]
    assert _calc_direction(data) == "flat"


def test_format_trends_for_prompt():
    """Test formatting trends as text for LLM prompt."""
    metrics = [
        MetricTrend(
            name="Revenue",
            unit="$B",
            data_points=[
                YearValue(year=2022, value=394_300_000_000, formatted="$394.3B"),
                YearValue(year=2023, value=383_300_000_000, formatted="$383.3B"),
            ],
            cagr=-2.8,
            trend_direction="down",
        ),
    ]
    text = _format_trends_for_prompt(metrics)
    assert "Revenue ($B):" in text
    assert "$394.3B" in text
    assert "CAGR: -2.8%" in text
    assert "Trend: down" in text


@pytest.mark.asyncio
@patch("sec_filing_agent.trends.get_company")
@patch("sec_filing_agent.trends.LLMClient")
async def test_analyze_trends_no_xbrl_data(mock_llm_cls, mock_get_company):
    """Test trend analysis when no XBRL data is available."""
    from sec_filing_agent.trends import analyze_trends

    # Mock company with no facts and no financials
    company = MagicMock()
    company.name = "Test Corp"
    company.get_facts.return_value = None
    company.get_financials.return_value = None
    mock_get_company.return_value = company

    report = await analyze_trends("TEST", years=5)
    assert report.ticker == "TEST"
    assert report.company_name == "Test Corp"
    assert report.metrics == []
    assert report.narrative == ""
