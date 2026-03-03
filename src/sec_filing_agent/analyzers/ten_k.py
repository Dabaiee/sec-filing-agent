"""10-K Annual Report Analyzer."""

from __future__ import annotations

import time
from typing import Any

from pydantic import BaseModel

from sec_filing_agent.analyzers.base import BaseAnalyzer
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.prompts import (
    TEN_K_ANALYSIS_PROMPT,
    TEN_K_FINANCIALS_PROMPT,
    TEN_K_RISK_FACTORS_PROMPT,
)
from sec_filing_agent.models.analysis import (
    AnalysisReport,
    FinancialHighlights,
    RiskFactor,
)
from sec_filing_agent.models.filing import FilingMetadata, RawFiling


class TenKAnalysisResponse(BaseModel):
    summary: str
    management_discussion: str
    forward_looking: list[str]


class TenKRiskResponse(BaseModel):
    risk_factors: list[RiskFactor]


class TenKFinancialsResponse(BaseModel):
    revenue: str | None = None
    net_income: str | None = None
    gross_margin: str | None = None
    operating_margin: str | None = None
    yoy_revenue_change: str | None = None
    key_metrics: dict[str, str] = {}


class TenKAnalyzer(BaseAnalyzer):
    """Analyzer for 10-K annual report filings."""

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
            "period_of_report": metadata.period_of_report,
            "content": filing.content[:80000],
        }

        # Stage 1: Main analysis (HIGH complexity — Sonnet)
        if on_stage_start:
            model_cfg = llm_client.router.route("ten_k_analysis")
            on_stage_start("Analyzing annual report", model_cfg.model)
        t0 = time.monotonic()

        analysis, _ = await llm_client.complete_structured(
            TEN_K_ANALYSIS_PROMPT.format(**prompt_context),
            TenKAnalysisResponse,
            "ten_k_analysis",
            "10-K Analysis",
        )

        if on_stage_complete:
            on_stage_complete("Analyzing annual report", time.monotonic() - t0)

        # Stage 2: Risk factors (HIGH complexity — Sonnet)
        if on_stage_start:
            model_cfg = llm_client.router.route("risk_factor_analysis")
            on_stage_start("Extracting risk factors", model_cfg.model)
        t0 = time.monotonic()

        risks, _ = await llm_client.complete_structured(
            TEN_K_RISK_FACTORS_PROMPT.format(**prompt_context),
            TenKRiskResponse,
            "risk_factor_analysis",
            "Risk Factor Analysis",
        )

        if on_stage_complete:
            on_stage_complete("Extracting risk factors", time.monotonic() - t0)

        # Stage 3: Financial extraction (LOW complexity — Haiku)
        if on_stage_start:
            model_cfg = llm_client.router.route("financial_extraction")
            on_stage_start("Extracting financial highlights", model_cfg.model)
        t0 = time.monotonic()

        financials, _ = await llm_client.complete_structured(
            TEN_K_FINANCIALS_PROMPT.format(**prompt_context),
            TenKFinancialsResponse,
            "financial_extraction",
            "Financial Extraction",
        )

        if on_stage_complete:
            on_stage_complete("Extracting financial highlights", time.monotonic() - t0)

        return AnalysisReport(
            ticker=metadata.ticker,
            company_name=metadata.company_name,
            filing_type=metadata.filing_type,
            filing_date=metadata.filing_date,
            period_of_report=metadata.period_of_report,
            summary=analysis.summary,
            risk_factors=risks.risk_factors[:5],
            financial_highlights=FinancialHighlights(
                revenue=financials.revenue,
                net_income=financials.net_income,
                gross_margin=financials.gross_margin,
                operating_margin=financials.operating_margin,
                yoy_revenue_change=financials.yoy_revenue_change,
                key_metrics=financials.key_metrics,
            ),
            management_discussion=analysis.management_discussion,
            forward_looking=analysis.forward_looking,
        )
