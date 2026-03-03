"""8-K Current Report Analyzer."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

from sec_filing_agent.analyzers.base import BaseAnalyzer
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.prompts import EIGHT_K_ANALYSIS_PROMPT, EIGHT_K_FINANCIALS_PROMPT
from sec_filing_agent.models.analysis import (
    AnalysisReport,
    FinancialHighlights,
    KeyEvent,
)
from sec_filing_agent.models.filing import FilingMetadata, RawFiling


class EightKAnalysisResponse(BaseModel):
    summary: str
    key_events: list[KeyEvent]


class EightKFinancialsResponse(BaseModel):
    revenue: str | None = None
    net_income: str | None = None
    gross_margin: str | None = None
    operating_margin: str | None = None
    yoy_revenue_change: str | None = None
    key_metrics: dict[str, str] = {}


class EightKAnalyzer(BaseAnalyzer):
    """Analyzer for 8-K current report filings.

    8-K filings are event-driven, so XBRL data is typically not available.
    Uses LLM for both event analysis and financial extraction.
    """

    async def analyze(
        self,
        filing: RawFiling,
        metadata: FilingMetadata,
        llm_client: LLMClient,
        on_stage_start: Any = None,
        on_stage_complete: Any = None,
    ) -> AnalysisReport:
        prompt_context = {
            "company_name": metadata.company_name,
            "ticker": metadata.ticker,
            "filing_date": str(metadata.filing_date),
            "content": filing.content[:80000],
        }

        # Stage 1: Event analysis (HIGH complexity — Sonnet)
        if on_stage_start:
            model_cfg = llm_client.router.route("eight_k_analysis")
            on_stage_start("Analyzing current report", model_cfg.model)
        t0 = time.monotonic()

        analysis, _ = await llm_client.complete_structured(
            EIGHT_K_ANALYSIS_PROMPT.format(**prompt_context),
            EightKAnalysisResponse,
            "eight_k_analysis",
            "8-K Analysis",
        )

        if on_stage_complete:
            on_stage_complete("Analyzing current report", time.monotonic() - t0)

        # Stage 2: Financial extraction (LOW complexity — Haiku)
        if on_stage_start:
            model_cfg = llm_client.router.route("financial_extraction")
            on_stage_start("Extracting financial data", model_cfg.model)
        t0 = time.monotonic()

        financials, _ = await llm_client.complete_structured(
            EIGHT_K_FINANCIALS_PROMPT.format(**prompt_context),
            EightKFinancialsResponse,
            "financial_extraction",
            "Financial Extraction",
        )

        if on_stage_complete:
            on_stage_complete("Extracting financial data", time.monotonic() - t0)

        return AnalysisReport(
            ticker=metadata.ticker,
            company_name=metadata.company_name,
            filing_type=metadata.filing_type,
            filing_date=metadata.filing_date,
            period_of_report=metadata.period_of_report,
            summary=analysis.summary,
            key_events=analysis.key_events,
            financial_highlights=FinancialHighlights(
                revenue=financials.revenue,
                net_income=financials.net_income,
                gross_margin=financials.gross_margin,
                operating_margin=financials.operating_margin,
                yoy_revenue_change=financials.yoy_revenue_change,
                key_metrics=financials.key_metrics,
            ),
        )
