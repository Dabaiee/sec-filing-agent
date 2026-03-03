"""Pydantic models for financial trend analysis."""

from __future__ import annotations

from pydantic import BaseModel, Field

from sec_filing_agent.models.analysis import ModelUsage


class YearValue(BaseModel):
    """A single year's data point for a metric."""

    year: int
    value: float
    formatted: str = Field(description="Human-readable value, e.g. '$394.3B'")


class MetricTrend(BaseModel):
    """A multi-year trend for a single financial metric."""

    name: str = Field(description="Metric name, e.g. 'Revenue'")
    unit: str = Field(description="Unit, e.g. '$B', '%', '$/share'")
    data_points: list[YearValue] = Field(default_factory=list)
    cagr: float | None = Field(default=None, description="Compound annual growth rate")
    trend_direction: str = Field(default="flat", description="up, down, flat, volatile")


class TrendReport(BaseModel):
    """Complete multi-year financial trend report."""

    ticker: str
    company_name: str
    years: int
    metrics: list[MetricTrend] = Field(default_factory=list)
    narrative: str = Field(default="", description="LLM-generated summary of trends")
    model_usage: ModelUsage = Field(default_factory=ModelUsage)
