"""Base analyzer interface for SEC filing analysis.

Architecture:
    Each filing type (10-K, 10-Q, 8-K) has a dedicated analyzer subclass.
    Analyzers follow a hybrid approach:
    1. XBRL structured data extraction (no LLM — 100% accurate financials)
    2. LLM qualitative analysis (risk factors, MD&A, forward-looking)
    3. LLM summary synthesis (combining structured + qualitative)

    New filing types can be added by:
    1. Subclassing BaseAnalyzer
    2. Implementing the analyze() method
    3. Registering via router.register_analyzer("TYPE", MyAnalyzer)
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Callable

from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.models.filing import FilingMetadata, RawFiling

# Callback type aliases for pipeline progress tracking
StageStartCallback = Callable[[str, str], None]  # (stage_name, model) -> None
StageCompleteCallback = Callable[[str, float], None]  # (stage_name, duration_s) -> None


class BaseAnalyzer(ABC):
    """Abstract base class for filing-type-specific analyzers.

    Subclasses implement multi-stage analysis pipelines that combine
    structured XBRL data extraction with LLM qualitative analysis.
    Each stage reports progress via optional callbacks.
    """

    @abstractmethod
    async def analyze(
        self,
        filing: RawFiling,
        metadata: FilingMetadata,
        llm_client: LLMClient,
        on_stage_start: StageStartCallback | None = None,
        on_stage_complete: StageCompleteCallback | None = None,
    ) -> AnalysisReport:
        """Analyze a filing and produce a structured report.

        Args:
            filing: The raw filing content from SEC EDGAR.
            metadata: Classified filing metadata (type, ticker, dates).
            llm_client: LLM client for API calls (handles routing and retries).
            on_stage_start: Optional callback(stage_name, model) when a stage begins.
            on_stage_complete: Optional callback(stage_name, duration_s) when done.

        Returns:
            Complete AnalysisReport with structured sections.
        """
        ...
