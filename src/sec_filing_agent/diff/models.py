"""Pydantic models for filing diff and comparison reports."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RiskChange(BaseModel):
    """A change in a risk factor between two filings."""

    change_type: str = Field(description="Type of change: added, removed, changed")
    title: str = Field(description="Risk factor title")
    description: str = Field(description="Description of the change")
    old_severity: str | None = Field(default=None, description="Previous severity")
    new_severity: str | None = Field(default=None, description="New severity")


class FinancialChange(BaseModel):
    """A change in a financial metric between two filings."""

    metric: str = Field(description="Metric name")
    old_value: str | None = Field(default=None, description="Previous value")
    new_value: str | None = Field(default=None, description="New value")
    change: str | None = Field(default=None, description="Change description (e.g., +2.5%)")


class DiffSummary(BaseModel):
    """LLM-generated summary of changes between two filings."""

    summary: str = Field(description="2-3 sentence overview of key changes")
    risk_changes: list[RiskChange] = Field(default_factory=list)
    financial_changes: list[FinancialChange] = Field(default_factory=list)
    notable_changes: list[str] = Field(default_factory=list, description="Other notable differences")


class DiffReport(BaseModel):
    """Report comparing two filings from the same company across time."""

    ticker: str
    company_name: str
    filing_type: str
    from_date: str
    to_date: str
    diff: DiffSummary
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0


class CompanyComparison(BaseModel):
    """LLM-generated comparison of two companies' filings."""

    summary: str = Field(description="2-3 sentence comparative overview")
    risk_comparison: list[str] = Field(default_factory=list, description="Key risk differences")
    financial_comparison: list[FinancialChange] = Field(default_factory=list)
    strengths_a: list[str] = Field(default_factory=list, description="Strengths of company A")
    strengths_b: list[str] = Field(default_factory=list, description="Strengths of company B")


class ComparisonReport(BaseModel):
    """Report comparing filings from two different companies."""

    ticker_a: str
    ticker_b: str
    company_a: str
    company_b: str
    filing_type: str
    comparison: CompanyComparison
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
