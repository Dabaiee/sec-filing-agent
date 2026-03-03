"""Base analyzer interface for SEC filing analysis."""

from __future__ import annotations

from abc import ABC, abstractmethod

from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.models.filing import FilingMetadata, RawFiling


class BaseAnalyzer(ABC):
    """Abstract base class for filing-type-specific analyzers."""

    @abstractmethod
    async def analyze(
        self,
        filing: RawFiling,
        metadata: FilingMetadata,
        llm_client: LLMClient,
        on_stage_start: object = None,
        on_stage_complete: object = None,
    ) -> AnalysisReport:
        """Analyze a filing and produce a structured report.

        Args:
            filing: The raw filing content.
            metadata: Classified filing metadata.
            llm_client: LLM client for API calls.
            on_stage_start: Optional callback(stage_name, model) when a stage begins.
            on_stage_complete: Optional callback(stage_name, duration_s) when a stage completes.

        Returns:
            Complete AnalysisReport.
        """
        ...
