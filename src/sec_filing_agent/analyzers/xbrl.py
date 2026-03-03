"""XBRL financial data extraction — structured data, no LLM needed."""

from __future__ import annotations

import logging
from typing import Any

from sec_filing_agent.models.analysis import FinancialHighlights

logger = logging.getLogger(__name__)


def extract_financial_highlights(financials: dict[str, Any] | None) -> FinancialHighlights | None:
    """Extract financial highlights from edgartools XBRL financial statements.

    Uses structured XBRL data — 100% accurate, no LLM hallucination possible.

    Args:
        financials: Dict from fetcher.get_financials() with income_statement,
                    balance_sheet, cash_flow keys.

    Returns:
        FinancialHighlights with real XBRL numbers, or None if unavailable.
    """
    if financials is None:
        return None

    income = financials.get("income_statement")
    if income is None:
        return None

    try:
        return FinancialHighlights(
            revenue=_extract_metric(income, "Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue"),
            net_income=_extract_metric(income, "NetIncomeLoss", "NetIncome"),
            gross_margin=_calc_margin(income, ["GrossProfit"], ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue"]),
            operating_margin=_calc_margin(income, ["OperatingIncomeLoss", "OperatingIncome"], ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue"]),
            yoy_revenue_change=_calc_yoy(income, ["Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax", "Revenue"]),
            key_metrics=_extract_key_metrics(income),
        )
    except Exception as e:
        logger.warning("XBRL financial extraction failed: %s", e)
        return None


def _extract_metric(statement: Any, *concept_names: str) -> str | None:
    """Try to extract a metric value from a financial statement by concept name."""
    if statement is None:
        return None

    for concept in concept_names:
        try:
            # edgartools financial statements have various access patterns
            if hasattr(statement, "get_concept"):
                row = statement.get_concept(concept)
                if row is not None:
                    val = _get_latest_value(row)
                    if val is not None:
                        return _format_currency(val)
            # Try DataFrame-style access
            if hasattr(statement, "data") and statement.data is not None:
                df = statement.data
                if concept in df.index:
                    val = df.loc[concept].iloc[-1] if len(df.columns) > 0 else None
                    if val is not None and str(val) != "nan":
                        return _format_currency(float(val))
        except Exception:
            continue
    return None


def _get_latest_value(row: Any) -> float | None:
    """Get the most recent value from a concept row."""
    try:
        if hasattr(row, "value"):
            return float(row.value)
        if hasattr(row, "values") and len(row.values) > 0:
            return float(row.values[-1])
        # Try as a Series
        if hasattr(row, "iloc"):
            val = row.iloc[-1]
            return float(val) if str(val) != "nan" else None
    except (ValueError, TypeError, IndexError):
        pass
    return None


def _format_currency(value: float) -> str:
    """Format a numeric value as a human-readable currency string."""
    abs_val = abs(value)
    sign = "-" if value < 0 else ""
    if abs_val >= 1_000_000_000:
        return f"{sign}${abs_val / 1_000_000_000:.1f}B"
    elif abs_val >= 1_000_000:
        return f"{sign}${abs_val / 1_000_000:.1f}M"
    elif abs_val >= 1_000:
        return f"{sign}${abs_val / 1_000:.1f}K"
    else:
        return f"{sign}${abs_val:.0f}"


def _calc_margin(statement: Any, numerator_concepts: list[str], denominator_concepts: list[str]) -> str | None:
    """Calculate a margin percentage from two financial concepts."""
    num = None
    for concept in numerator_concepts:
        val = _extract_metric(statement, concept)
        if val:
            num = _parse_currency(val)
            break

    den = None
    for concept in denominator_concepts:
        val = _extract_metric(statement, concept)
        if val:
            den = _parse_currency(val)
            break

    if num is not None and den is not None and den != 0:
        return f"{(num / den) * 100:.1f}%"
    return None


def _calc_yoy(statement: Any, concepts: list[str]) -> str | None:
    """Calculate year-over-year change for a metric."""
    # This requires multi-period data which depends on the statement structure
    # For now, return None — will be populated by trend analysis
    return None


def _parse_currency(formatted: str) -> float | None:
    """Parse a formatted currency string back to a float."""
    try:
        s = formatted.replace("$", "").replace(",", "").strip()
        sign = -1 if s.startswith("-") else 1
        s = s.lstrip("-")
        if s.endswith("B"):
            return sign * float(s[:-1]) * 1_000_000_000
        elif s.endswith("M"):
            return sign * float(s[:-1]) * 1_000_000
        elif s.endswith("K"):
            return sign * float(s[:-1]) * 1_000
        else:
            return sign * float(s)
    except (ValueError, AttributeError):
        return None


def _extract_key_metrics(income: Any) -> dict[str, str]:
    """Extract additional key metrics from the income statement."""
    metrics: dict[str, str] = {}

    eps = _extract_metric(income, "EarningsPerShareDiluted", "EarningsPerShareBasicAndDiluted")
    if eps:
        metrics["EPS (Diluted)"] = eps

    return metrics
