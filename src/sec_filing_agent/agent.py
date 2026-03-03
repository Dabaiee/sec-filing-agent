"""High-level Agent SDK for programmatic access to SEC filing analysis."""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Any, AsyncIterator

from sec_filing_agent.models.analysis import AnalysisReport, ModelUsage
from sec_filing_agent.models.config import Settings


@dataclass
class StageEvent:
    """Event emitted during pipeline streaming."""

    name: str
    status: str  # "started", "completed"
    model: str | None = None
    duration_s: float | None = None


class Agent:
    """High-level SDK for SEC filing analysis.

    Usage::

        agent = Agent(model="claude-sonnet")

        # Single analysis
        report = await agent.analyze("AAPL", filing_type="10-K")
        print(report.risk_factors[0].severity)

        # Batch analysis
        reports = await agent.analyze_batch(["AAPL", "MSFT", "NVDA"])

        # Streaming
        async for stage in agent.analyze_stream("AAPL"):
            print(f"{stage.name}: {stage.status}")

        # Comparison
        diff = await agent.diff("AAPL", from_period="2023", to_period="2024")
    """

    def __init__(self, model: str | None = None, api_key: str | None = None) -> None:
        """Initialize the Agent.

        Args:
            model: Optional model override (e.g., "claude-sonnet-4-20250514").
            api_key: Optional Anthropic API key. Uses ANTHROPIC_API_KEY env var if not set.
        """
        self._settings = Settings.from_env()
        if api_key:
            self._settings.anthropic_api_key = api_key
        if model:
            self._settings.sec_agent_model = model

    async def analyze(
        self,
        ticker: str,
        filing_type: str | None = None,
    ) -> AnalysisReport:
        """Analyze the latest SEC filing for a ticker.

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL").
            filing_type: Optional filing type filter ("10-K", "10-Q", "8-K").

        Returns:
            AnalysisReport with structured analysis results.
        """
        return await self._run_pipeline(ticker, filing_type=filing_type)

    def analyze_sync(
        self,
        ticker: str,
        filing_type: str | None = None,
    ) -> AnalysisReport:
        """Synchronous wrapper for analyze().

        Args:
            ticker: Stock ticker symbol (e.g., "AAPL").
            filing_type: Optional filing type filter.

        Returns:
            AnalysisReport with structured analysis results.
        """
        return asyncio.run(self.analyze(ticker, filing_type=filing_type))

    async def analyze_batch(
        self,
        tickers: list[str],
        filing_type: str | None = None,
    ) -> list[AnalysisReport]:
        """Analyze multiple tickers sequentially.

        Args:
            tickers: List of ticker symbols.
            filing_type: Optional filing type filter applied to all.

        Returns:
            List of AnalysisReport objects (one per ticker).
        """
        results = []
        for ticker in tickers:
            report = await self.analyze(ticker, filing_type=filing_type)
            results.append(report)
        return results

    async def analyze_stream(
        self,
        ticker: str,
        filing_type: str | None = None,
    ) -> AsyncIterator[StageEvent]:
        """Analyze a filing with streaming stage events.

        Yields StageEvent objects as each pipeline stage starts and completes.
        The final event contains the complete AnalysisReport in its `report` attribute.

        Args:
            ticker: Stock ticker symbol.
            filing_type: Optional filing type filter.

        Yields:
            StageEvent for each pipeline stage transition.
        """
        from sec_filing_agent.classifier import classify_filing
        from sec_filing_agent.fetcher import fetch_latest_filing
        from sec_filing_agent.llm.client import LLMClient
        from sec_filing_agent.llm.model_router import ModelRouter
        from sec_filing_agent.router import get_analyzer

        pipeline_start = time.monotonic()

        # Fetch
        yield StageEvent(name="Fetching filing", status="started", model="httpx")
        t0 = time.monotonic()
        raw_filing = await fetch_latest_filing(ticker, filing_type=filing_type, settings=self._settings)
        yield StageEvent(name="Fetching filing", status="completed", duration_s=time.monotonic() - t0)

        # Classify
        yield StageEvent(name="Classifying filing", status="started", model="heuristic")
        t0 = time.monotonic()
        metadata = classify_filing(raw_filing)
        yield StageEvent(name="Classifying filing", status="completed", duration_s=time.monotonic() - t0)

        # Route
        yield StageEvent(name="Routing to analyzer", status="started", model="router")
        analyzer = get_analyzer(metadata.filing_type)
        yield StageEvent(name="Routing to analyzer", status="completed", duration_s=0.0)

        # Analyze
        llm_client = LLMClient(settings=self._settings)

        # Track LLM stage events
        events: list[StageEvent] = []

        def on_stage_start(name: str, model: str) -> None:
            events.append(StageEvent(name=name, status="started", model=model))

        def on_stage_complete(name: str, duration: float) -> None:
            events.append(StageEvent(name=name, status="completed", duration_s=duration))

        report = await analyzer.analyze(
            raw_filing, metadata, llm_client,
            on_stage_start=on_stage_start,
            on_stage_complete=on_stage_complete,
        )

        for event in events:
            yield event

        # Finalize usage
        total_input = sum(s.input_tokens for s in llm_client.usage_log)
        total_output = sum(s.output_tokens for s in llm_client.usage_log)
        total_cost = sum(
            ModelRouter.estimate_cost(s.model, s.input_tokens, s.output_tokens)
            for s in llm_client.usage_log
        )
        report.model_usage = ModelUsage(
            stages=llm_client.usage_log,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            estimated_cost_usd=round(total_cost, 4),
        )
        report.pipeline_duration_ms = int((time.monotonic() - pipeline_start) * 1000)

        yield StageEvent(name="complete", status="completed")

    async def diff(
        self,
        ticker: str,
        filing_type: str = "10-K",
        from_period: str = "",
        to_period: str = "",
    ) -> Any:
        """Compare a company's filings across time periods.

        Args:
            ticker: Stock ticker symbol.
            filing_type: Filing type to compare.
            from_period: Date hint for earlier filing (e.g., "2023").
            to_period: Date hint for later filing (e.g., "2024").

        Returns:
            DiffReport with the comparison.
        """
        from sec_filing_agent.diff.analyzer import diff_filings
        return await diff_filings(
            ticker=ticker,
            filing_type=filing_type,
            from_hint=from_period,
            to_hint=to_period,
            settings=self._settings,
        )

    async def compare(
        self,
        ticker_a: str,
        ticker_b: str,
        filing_type: str = "10-K",
    ) -> Any:
        """Compare filings of two different companies.

        Args:
            ticker_a: First company ticker.
            ticker_b: Second company ticker.
            filing_type: Filing type to compare.

        Returns:
            ComparisonReport with the comparison.
        """
        from sec_filing_agent.diff.analyzer import compare_companies
        return await compare_companies(
            ticker_a=ticker_a,
            ticker_b=ticker_b,
            filing_type=filing_type,
            settings=self._settings,
        )

    async def _run_pipeline(
        self,
        ticker: str,
        filing_type: str | None = None,
    ) -> AnalysisReport:
        """Run the full analysis pipeline without terminal UI."""
        from sec_filing_agent.classifier import classify_filing
        from sec_filing_agent.fetcher import fetch_latest_filing
        from sec_filing_agent.llm.client import LLMClient
        from sec_filing_agent.llm.model_router import ModelRouter
        from sec_filing_agent.router import get_analyzer

        pipeline_start = time.monotonic()

        raw_filing = await fetch_latest_filing(ticker, filing_type=filing_type, settings=self._settings)
        metadata = classify_filing(raw_filing)
        analyzer = get_analyzer(metadata.filing_type)

        llm_client = LLMClient(settings=self._settings)
        report = await analyzer.analyze(raw_filing, metadata, llm_client)

        # Compute aggregate usage
        total_input = sum(s.input_tokens for s in llm_client.usage_log)
        total_output = sum(s.output_tokens for s in llm_client.usage_log)
        total_cost = sum(
            ModelRouter.estimate_cost(s.model, s.input_tokens, s.output_tokens)
            for s in llm_client.usage_log
        )
        report.model_usage = ModelUsage(
            stages=llm_client.usage_log,
            total_input_tokens=total_input,
            total_output_tokens=total_output,
            estimated_cost_usd=round(total_cost, 4),
        )
        report.pipeline_duration_ms = int((time.monotonic() - pipeline_start) * 1000)

        return report
