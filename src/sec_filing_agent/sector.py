"""Sector peer comparison analysis using XBRL financial data."""

from __future__ import annotations

import logging
from typing import Any

from sec_filing_agent.analyzers.xbrl import extract_financial_highlights
from sec_filing_agent.fetcher import get_company, get_financials
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.model_router import ModelRouter
from sec_filing_agent.models.analysis import ModelUsage
from sec_filing_agent.models.config import Settings
from sec_filing_agent.models.sector import PeerMetrics, SectorReport

logger = logging.getLogger(__name__)

# Default sector peer mappings
SECTOR_PEERS: dict[str, list[str]] = {
    "Technology": ["AAPL", "MSFT", "GOOG", "META", "NVDA", "AMZN"],
    "Finance": ["JPM", "BAC", "GS", "MS", "C", "WFC"],
    "Healthcare": ["JNJ", "UNH", "PFE", "ABBV", "MRK", "LLY"],
    "Energy": ["XOM", "CVX", "COP", "SLB", "EOG", "MPC"],
    "Consumer": ["WMT", "PG", "KO", "PEP", "COST", "TGT"],
    "Industrial": ["CAT", "HON", "UPS", "BA", "GE", "RTX"],
}

# SIC code to sector mapping (simplified)
SIC_SECTOR: dict[str, str] = {
    "73": "Technology",
    "36": "Technology",
    "35": "Technology",
    "37": "Industrial",
    "28": "Healthcare",
    "60": "Finance",
    "61": "Finance",
    "62": "Finance",
    "13": "Energy",
    "29": "Energy",
    "20": "Consumer",
    "51": "Consumer",
    "53": "Consumer",
}

SECTOR_NARRATIVE_PROMPT = """\
You are a financial analyst. Compare {company_name} ({ticker}) against its sector peers.

Financial data for each company:
{peer_data}

Respond with a JSON object:
{{
  "narrative": "<2-3 paragraph competitive positioning analysis. Compare revenue scale, \
margins, and growth. Identify relative strengths and weaknesses.>"
}}
"""


async def analyze_sector(
    ticker: str,
    peers: list[str] | None = None,
    settings: Settings | None = None,
) -> SectorReport:
    """Compare a company against sector peers using XBRL data.

    Args:
        ticker: Stock ticker symbol.
        peers: Optional list of peer tickers. Auto-detected if not provided.
        settings: Optional settings override.

    Returns:
        SectorReport with peer metrics and narrative.
    """
    if settings is None:
        settings = Settings.from_env()

    company = await get_company(ticker, settings)
    sector = _detect_sector(company)

    if peers is None:
        peers = _get_default_peers(ticker, sector)

    # Gather all tickers to analyze
    all_tickers = [ticker] + [p for p in peers if p.upper() != ticker.upper()]

    # Fetch financials for all companies
    peer_metrics: list[PeerMetrics] = []
    for t in all_tickers:
        metrics = await _get_peer_metrics(t, settings)
        if metrics:
            peer_metrics.append(metrics)

    # Generate LLM narrative
    narrative = ""
    model_usage = ModelUsage()
    if len(peer_metrics) >= 2:
        try:
            llm_client = LLMClient(settings=settings)
            peer_text = _format_peers_for_prompt(peer_metrics)

            from pydantic import BaseModel

            class NarrativeModel(BaseModel):
                narrative: str

            prompt = SECTOR_NARRATIVE_PROMPT.format(
                company_name=company.name,
                ticker=ticker.upper(),
                peer_data=peer_text,
            )
            result, usage = await llm_client.complete_structured(
                prompt, NarrativeModel, "basic_summarization", "Sector Narrative"
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
            logger.warning("Failed to generate sector narrative: %s", e)

    return SectorReport(
        ticker=ticker.upper(),
        company_name=company.name,
        sector=sector,
        peers=peer_metrics,
        narrative=narrative,
        model_usage=model_usage,
    )


def _detect_sector(company: Any) -> str:
    """Detect sector from company SIC code."""
    try:
        sic = str(company.sic)[:2] if company.sic else ""
        return SIC_SECTOR.get(sic, "Technology")
    except Exception:
        return "Technology"


def _get_default_peers(ticker: str, sector: str) -> list[str]:
    """Get default peers for a sector, excluding the target ticker."""
    peers = SECTOR_PEERS.get(sector, SECTOR_PEERS.get("Technology", []))
    return [p for p in peers if p.upper() != ticker.upper()][:5]


async def _get_peer_metrics(ticker: str, settings: Settings) -> PeerMetrics | None:
    """Fetch financial metrics for a single peer."""
    try:
        company = await get_company(ticker, settings)
        financials_data = await get_financials(ticker, settings)
        highlights = extract_financial_highlights(financials_data)

        return PeerMetrics(
            ticker=ticker.upper(),
            company_name=company.name,
            revenue=highlights.revenue if highlights else None,
            net_income=highlights.net_income if highlights else None,
            gross_margin=highlights.gross_margin if highlights else None,
            operating_margin=highlights.operating_margin if highlights else None,
        )
    except Exception as e:
        logger.warning("Failed to fetch metrics for %s: %s", ticker, e)
        return PeerMetrics(ticker=ticker.upper(), company_name=ticker.upper())


def _format_peers_for_prompt(peers: list[PeerMetrics]) -> str:
    """Format peer metrics as text for the LLM prompt."""
    lines = []
    for p in peers:
        parts = [f"{p.ticker} ({p.company_name})"]
        if p.revenue:
            parts.append(f"Revenue: {p.revenue}")
        if p.net_income:
            parts.append(f"Net Income: {p.net_income}")
        if p.gross_margin:
            parts.append(f"Gross Margin: {p.gross_margin}")
        if p.operating_margin:
            parts.append(f"Operating Margin: {p.operating_margin}")
        lines.append(" | ".join(parts))
    return "\n".join(lines)
