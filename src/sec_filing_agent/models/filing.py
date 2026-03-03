"""Pydantic models for SEC filings and metadata."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class RawFiling(BaseModel):
    """Raw filing content fetched from SEC EDGAR."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    ticker: str = Field(description="Stock ticker symbol")
    cik: str = Field(description="Central Index Key")
    company_name: str = Field(description="Company name from EDGAR")
    accession_number: str = Field(description="SEC accession number")
    filing_type: str = Field(description="Filing form type (e.g., 10-K, 10-Q, 8-K)")
    filing_date: date = Field(description="Date the filing was submitted")
    document_url: str = Field(description="URL of the primary document")
    content: str = Field(description="Raw text content of the filing")
    filing_obj: Any = Field(default=None, description="Original edgartools Filing object")


class FilingMetadata(BaseModel):
    """Classified filing metadata."""

    filing_type: str = Field(description="Detected filing type: 10-K, 10-Q, or 8-K")
    company_name: str = Field(description="Company name")
    ticker: str = Field(description="Stock ticker symbol")
    cik: str = Field(description="Central Index Key")
    filing_date: date = Field(description="Date filed with SEC")
    period_of_report: str = Field(description="Reporting period covered")
