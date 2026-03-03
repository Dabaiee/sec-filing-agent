"""Tests for sector peer comparison analysis."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from sec_filing_agent.sector import (
    _detect_sector,
    _format_peers_for_prompt,
    _get_default_peers,
)
from sec_filing_agent.models.sector import PeerMetrics


def _make_mock_company(sic: str = "73", name: str = "Test Corp"):
    """Create a mock company with a SIC code."""
    company = MagicMock()
    company.sic = sic
    company.name = name
    return company


def test_detect_sector_technology():
    """SIC code 73xx maps to Technology."""
    company = _make_mock_company(sic="7372")
    assert _detect_sector(company) == "Technology"


def test_detect_sector_finance():
    """SIC code 60xx maps to Finance."""
    company = _make_mock_company(sic="6020")
    assert _detect_sector(company) == "Finance"


def test_detect_sector_healthcare():
    """SIC code 28xx maps to Healthcare."""
    company = _make_mock_company(sic="2834")
    assert _detect_sector(company) == "Healthcare"


def test_detect_sector_unknown_defaults_to_technology():
    """Unknown SIC code defaults to Technology."""
    company = _make_mock_company(sic="9999")
    assert _detect_sector(company) == "Technology"


def test_detect_sector_no_sic():
    """Company with no SIC defaults to Technology."""
    company = MagicMock()
    company.sic = None
    assert _detect_sector(company) == "Technology"


def test_get_default_peers_excludes_target():
    """Default peers exclude the target ticker."""
    peers = _get_default_peers("AAPL", "Technology")
    assert "AAPL" not in peers
    assert len(peers) <= 5


def test_get_default_peers_technology():
    """Technology sector returns tech peers."""
    peers = _get_default_peers("AAPL", "Technology")
    assert any(p in peers for p in ["MSFT", "GOOG", "META", "NVDA", "AMZN"])


def test_get_default_peers_unknown_sector():
    """Unknown sector falls back to Technology peers."""
    peers = _get_default_peers("XYZ", "Unknown")
    # Should return Technology sector peers as fallback
    assert len(peers) > 0


def test_format_peers_basic():
    """Test formatting peer metrics for LLM prompt."""
    peers = [
        PeerMetrics(
            ticker="AAPL",
            company_name="Apple Inc.",
            revenue="$394.3B",
            net_income="$93.7B",
            gross_margin="46.2%",
        ),
        PeerMetrics(
            ticker="MSFT",
            company_name="Microsoft Corp",
            revenue="$245.1B",
        ),
    ]
    text = _format_peers_for_prompt(peers)
    assert "AAPL (Apple Inc.)" in text
    assert "Revenue: $394.3B" in text
    assert "MSFT (Microsoft Corp)" in text
    assert "Revenue: $245.1B" in text


def test_format_peers_no_data():
    """Peers with no financial data show just ticker."""
    peers = [PeerMetrics(ticker="XYZ", company_name="Unknown Corp")]
    text = _format_peers_for_prompt(peers)
    assert "XYZ (Unknown Corp)" in text


@pytest.mark.asyncio
@patch("sec_filing_agent.sector.get_company")
@patch("sec_filing_agent.sector._get_peer_metrics")
@patch("sec_filing_agent.sector.LLMClient")
async def test_analyze_sector_basic(mock_llm_cls, mock_get_metrics, mock_get_company):
    """Test basic sector analysis with mocked dependencies."""
    from sec_filing_agent.sector import analyze_sector

    company = _make_mock_company(sic="7372", name="Apple Inc.")
    mock_get_company.return_value = company

    mock_get_metrics.return_value = PeerMetrics(
        ticker="AAPL", company_name="Apple Inc.", revenue="$394.3B"
    )

    report = await analyze_sector("AAPL", peers=["MSFT"])
    assert report.ticker == "AAPL"
    assert report.company_name == "Apple Inc."
    assert report.sector == "Technology"
    assert len(report.peers) >= 1
