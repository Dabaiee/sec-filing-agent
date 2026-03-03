"""Pydantic models for analysis reports and LLM outputs."""

from __future__ import annotations

from datetime import date

from pydantic import BaseModel, Field


class RiskFactor(BaseModel):
    """A categorized risk factor from a filing."""

    category: str = Field(description="Risk category: regulatory, market, operational, financial, competitive")
    title: str = Field(description="Short risk title")
    description: str = Field(description="Detailed risk description")
    severity: str = Field(description="Severity level: high, medium, low")


class FinancialHighlights(BaseModel):
    """Key financial metrics extracted from a filing."""

    revenue: str | None = Field(default=None, description="Total revenue")
    net_income: str | None = Field(default=None, description="Net income")
    gross_margin: str | None = Field(default=None, description="Gross margin percentage")
    operating_margin: str | None = Field(default=None, description="Operating margin percentage")
    yoy_revenue_change: str | None = Field(default=None, description="Year-over-year revenue change")
    key_metrics: dict[str, str] = Field(default_factory=dict, description="Additional key metrics")


class KeyEvent(BaseModel):
    """A key event from an 8-K filing."""

    event_type: str = Field(description="Event type: earnings, acquisition, leadership, restructuring, other")
    headline: str = Field(description="Event headline")
    details: str = Field(description="Event details")
    material_impact: str = Field(description="Material impact: high, medium, low")


class StageUsage(BaseModel):
    """Token usage for a single pipeline stage."""

    stage: str = Field(description="Pipeline stage name")
    model: str = Field(description="Model used for this stage")
    input_tokens: int = Field(description="Input tokens consumed")
    output_tokens: int = Field(description="Output tokens generated")


class ModelUsage(BaseModel):
    """Aggregate model usage across all pipeline stages."""

    stages: list[StageUsage] = Field(default_factory=list, description="Per-stage usage breakdown")
    total_input_tokens: int = Field(default=0, description="Total input tokens")
    total_output_tokens: int = Field(default=0, description="Total output tokens")
    estimated_cost_usd: float = Field(default=0.0, description="Estimated cost in USD")


class AnalysisReport(BaseModel):
    """Complete analysis report for an SEC filing."""

    ticker: str = Field(description="Stock ticker symbol")
    company_name: str = Field(description="Company name")
    filing_type: str = Field(description="Filing type: 10-K, 10-Q, 8-K")
    filing_date: date = Field(description="Filing date")
    period_of_report: str = Field(description="Reporting period covered")
    summary: str = Field(description="2-3 sentence executive summary")

    # Filing-type-specific sections
    risk_factors: list[RiskFactor] | None = Field(default=None, description="Top risk factors (10-K)")
    financial_highlights: FinancialHighlights | None = Field(default=None, description="Financial metrics")
    key_events: list[KeyEvent] | None = Field(default=None, description="Key events (8-K)")
    management_discussion: str | None = Field(default=None, description="MD&A key points")
    forward_looking: list[str] | None = Field(default=None, description="Forward-looking statements")

    # Metadata
    model_usage: ModelUsage = Field(default_factory=ModelUsage, description="Model usage statistics")
    pipeline_duration_ms: int = Field(default=0, description="Total pipeline duration in milliseconds")
