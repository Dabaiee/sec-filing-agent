"""Multi-year financial trend analysis using XBRL data."""

from __future__ import annotations

import logging
import math
from typing import Any

from sec_filing_agent.analyzers.xbrl import _format_currency
from sec_filing_agent.fetcher import get_company
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.model_router import ModelRouter
from sec_filing_agent.models.analysis import ModelUsage
from sec_filing_agent.models.config import Settings
from sec_filing_agent.models.trends import MetricTrend, TrendReport, YearValue

logger = logging.getLogger(__name__)

# XBRL concepts to fetch for trend analysis
TREND_CONCEPTS = [
    ("Revenues", "Revenue", "$"),
    ("NetIncomeLoss", "Net Income", "$"),
    ("GrossProfit", "Gross Profit", "$"),
    ("OperatingIncomeLoss", "Operating Income", "$"),
    ("EarningsPerShareDiluted", "EPS (Diluted)", "$/share"),
]

TREND_NARRATIVE_PROMPT = """\
You are a financial analyst. Given the following multi-year financial trend data for \
{company_name} ({ticker}), write a brief 2-3 sentence analysis of the key trends.

{trend_data}

Respond with a JSON object:
{{
  "narrative": "<2-3 sentence analysis of the key trends, highlighting notable changes>"
}}
"""


class NarrativeResponse:
    """Simple container for LLM narrative response."""


async def analyze_trends(
    ticker: str,
    years: int = 5,
    settings: Settings | None = None,
) -> TrendReport:
    """Analyze multi-year financial trends using XBRL data.

    Args:
        ticker: Stock ticker symbol.
        years: Number of years of data to include.
        settings: Optional settings override.

    Returns:
        TrendReport with metrics and narrative.
    """
    if settings is None:
        settings = Settings.from_env()

    company = await get_company(ticker, settings)
    facts = company.get_facts()

    metrics: list[MetricTrend] = []

    if facts is not None:
        for concept_name, display_name, unit_prefix in TREND_CONCEPTS:
            trend = _extract_trend(facts, concept_name, display_name, unit_prefix, years)
            if trend and len(trend.data_points) >= 2:
                metrics.append(trend)

    # If no XBRL facts available, try get_financials
    if not metrics:
        financials = company.get_financials()
        if financials is not None:
            metrics = _extract_trends_from_financials(financials, years)

    # Generate narrative using LLM
    narrative = ""
    model_usage = ModelUsage()
    if metrics:
        try:
            llm_client = LLMClient(settings=settings)
            trend_text = _format_trends_for_prompt(metrics)
            from pydantic import BaseModel

            class NarrativeModel(BaseModel):
                narrative: str

            prompt = TREND_NARRATIVE_PROMPT.format(
                company_name=company.name,
                ticker=ticker.upper(),
                trend_data=trend_text,
            )
            result, usage = await llm_client.complete_structured(
                prompt, NarrativeModel, "basic_summarization", "Trend Narrative"
            )
            narrative = result.narrative
            cost = ModelRouter.estimate_cost(usage.model, usage.input_tokens, usage.output_tokens)
            model_usage = ModelUsage(
                stages=[usage],
                total_input_tokens=usage.input_tokens,
                total_output_tokens=usage.output_tokens,
                estimated_cost_usd=round(cost, 4),
            )
        except Exception as e:
            logger.warning("Failed to generate trend narrative: %s", e)

    return TrendReport(
        ticker=ticker.upper(),
        company_name=company.name,
        years=years,
        metrics=metrics,
        narrative=narrative,
        model_usage=model_usage,
    )


def _extract_trend(
    facts: Any, concept: str, display_name: str, unit_prefix: str, years: int
) -> MetricTrend | None:
    """Extract a multi-year trend for a single concept from XBRL facts."""
    try:
        # Try to get annual data for the concept
        if hasattr(facts, "to_pandas"):
            df = facts.to_pandas(f"us-gaap:{concept}")
            if df is not None and len(df) > 0:
                return _trend_from_dataframe(df, display_name, unit_prefix, years)
    except Exception:
        pass

    try:
        # Alternative access pattern
        if hasattr(facts, "get"):
            concept_data = facts.get(f"us-gaap:{concept}")
            if concept_data is not None:
                return _trend_from_concept_data(concept_data, display_name, unit_prefix, years)
    except Exception:
        pass

    return None


def _trend_from_dataframe(df: Any, name: str, unit_prefix: str, years: int) -> MetricTrend | None:
    """Build a MetricTrend from a pandas DataFrame."""
    try:
        # Filter to annual periods and recent years
        data_points: list[YearValue] = []
        seen_years: set[int] = set()

        for _, row in df.iterrows():
            try:
                year = None
                val = None
                # Try common column names
                for date_col in ["end", "filed", "period_end", "date"]:
                    if date_col in df.columns:
                        date_val = row[date_col]
                        if hasattr(date_val, "year"):
                            year = date_val.year
                        break
                for val_col in ["val", "value", "amount"]:
                    if val_col in df.columns:
                        val = float(row[val_col])
                        break

                if year and val and year not in seen_years:
                    seen_years.add(year)
                    if unit_prefix == "$":
                        formatted = _format_currency(val)
                    elif unit_prefix == "$/share":
                        formatted = f"${val:.2f}"
                    else:
                        formatted = f"{val:.1f}%"
                    data_points.append(YearValue(year=year, value=val, formatted=formatted))
            except (ValueError, TypeError):
                continue

        # Sort by year, keep latest N
        data_points.sort(key=lambda x: x.year)
        data_points = data_points[-years:]

        if len(data_points) < 2:
            return None

        unit = "$B" if unit_prefix == "$" and any(abs(d.value) > 1e9 for d in data_points) else unit_prefix
        cagr = _calc_cagr(data_points)
        direction = _calc_direction(data_points)

        return MetricTrend(
            name=name, unit=unit, data_points=data_points, cagr=cagr, trend_direction=direction
        )
    except Exception:
        return None


def _trend_from_concept_data(data: Any, name: str, unit_prefix: str, years: int) -> MetricTrend | None:
    """Build a MetricTrend from edgartools concept data."""
    # Fallback — concept data structures vary
    return None


def _extract_trends_from_financials(financials: Any, years: int) -> list[MetricTrend]:
    """Extract trends from edgartools Financials object as fallback."""
    # Financials may have multi-period data in columns
    return []


def _calc_cagr(data_points: list[YearValue]) -> float | None:
    """Calculate compound annual growth rate."""
    if len(data_points) < 2:
        return None
    first = data_points[0].value
    last = data_points[-1].value
    n_years = data_points[-1].year - data_points[0].year
    if n_years <= 0 or first <= 0 or last <= 0:
        return None
    try:
        return (math.pow(last / first, 1 / n_years) - 1) * 100
    except (ValueError, ZeroDivisionError):
        return None


def _calc_direction(data_points: list[YearValue]) -> str:
    """Determine trend direction from data points."""
    if len(data_points) < 2:
        return "flat"
    values = [d.value for d in data_points]
    increases = sum(1 for i in range(1, len(values)) if values[i] > values[i - 1])
    decreases = sum(1 for i in range(1, len(values)) if values[i] < values[i - 1])
    total = len(values) - 1
    if increases > total * 0.6:
        return "up"
    elif decreases > total * 0.6:
        return "down"
    elif increases > 0 and decreases > 0:
        return "volatile"
    return "flat"


def _format_trends_for_prompt(metrics: list[MetricTrend]) -> str:
    """Format trend data as text for the LLM prompt."""
    lines = []
    for m in metrics:
        lines.append(f"{m.name} ({m.unit}):")
        for dp in m.data_points:
            lines.append(f"  {dp.year}: {dp.formatted}")
        if m.cagr is not None:
            lines.append(f"  CAGR: {m.cagr:.1f}%")
        lines.append(f"  Trend: {m.trend_direction}")
        lines.append("")
    return "\n".join(lines)
