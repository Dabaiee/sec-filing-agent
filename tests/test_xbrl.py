"""Tests for XBRL financial data extraction."""

from __future__ import annotations

from unittest.mock import MagicMock

from sec_filing_agent.analyzers.xbrl import (
    _format_currency,
    _parse_currency,
    extract_financial_highlights,
)


def _make_mock_income_statement(
    revenue: float = 394_300_000_000,
    net_income: float = 93_700_000_000,
    gross_profit: float = 182_200_000_000,
    operating_income: float = 118_700_000_000,
):
    """Create a mock income statement with get_concept support."""
    statement = MagicMock()

    def make_row(value: float):
        row = MagicMock()
        row.value = value
        return row

    concept_map = {
        "Revenues": make_row(revenue),
        "NetIncomeLoss": make_row(net_income),
        "GrossProfit": make_row(gross_profit),
        "OperatingIncomeLoss": make_row(operating_income),
    }

    def get_concept(name: str):
        return concept_map.get(name)

    statement.get_concept = get_concept
    statement.data = None
    return statement


def test_format_currency_billions():
    assert _format_currency(394_300_000_000) == "$394.3B"


def test_format_currency_millions():
    assert _format_currency(96_200_000) == "$96.2M"


def test_format_currency_thousands():
    assert _format_currency(5_500) == "$5.5K"


def test_format_currency_small():
    assert _format_currency(42) == "$42"


def test_format_currency_negative():
    assert _format_currency(-1_200_000_000) == "-$1.2B"


def test_parse_currency_billions():
    assert _parse_currency("$394.3B") == 394_300_000_000


def test_parse_currency_millions():
    assert _parse_currency("$96.2M") == 96_200_000


def test_parse_currency_negative():
    assert _parse_currency("-$1.2B") == -1_200_000_000


def test_parse_currency_none_on_invalid():
    assert _parse_currency("invalid") is None


def test_extract_financial_highlights_none_input():
    assert extract_financial_highlights(None) is None


def test_extract_financial_highlights_no_income():
    assert extract_financial_highlights({"balance_sheet": MagicMock()}) is None


def test_extract_financial_highlights_with_data():
    income = _make_mock_income_statement()
    result = extract_financial_highlights({"income_statement": income})

    assert result is not None
    assert result.revenue == "$394.3B"
    assert result.net_income == "$93.7B"
    assert result.gross_margin is not None
    assert result.operating_margin is not None
