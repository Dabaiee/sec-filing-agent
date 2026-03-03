"""Pydantic models for sector peer comparison."""

from __future__ import annotations

from pydantic import BaseModel, Field

from sec_filing_agent.models.analysis import ModelUsage


class PeerMetrics(BaseModel):
    """Financial metrics for a single company in a peer comparison."""

    ticker: str
    company_name: str
    revenue: str | None = None
    net_income: str | None = None
    gross_margin: str | None = None
    operating_margin: str | None = None


class SectorReport(BaseModel):
    """Sector peer comparison report."""

    ticker: str
    company_name: str
    sector: str = ""
    peers: list[PeerMetrics] = Field(default_factory=list)
    narrative: str = Field(default="", description="LLM-generated competitive positioning")
    model_usage: ModelUsage = Field(default_factory=ModelUsage)
