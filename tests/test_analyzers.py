"""Tests for filing analyzers with mocked LLM responses."""

from __future__ import annotations

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from sec_filing_agent.analyzers.ten_k import TenKAnalyzer
from sec_filing_agent.analyzers.ten_q import TenQAnalyzer
from sec_filing_agent.analyzers.eight_k import EightKAnalyzer
from sec_filing_agent.llm.client import LLMClient
from sec_filing_agent.llm.model_router import ModelConfig
from sec_filing_agent.models.analysis import StageUsage
from sec_filing_agent.models.filing import FilingMetadata, RawFiling

from tests.mock_data import (
    MOCK_10K_ANALYSIS_JSON,
    MOCK_10K_FINANCIALS_JSON,
    MOCK_10K_RISKS_JSON,
    MOCK_10Q_ANALYSIS_JSON,
    MOCK_10Q_FINANCIALS_JSON,
    MOCK_8K_ANALYSIS_JSON,
    MOCK_8K_FINANCIALS_JSON,
)


def _make_mock_llm(responses: list[str]) -> MagicMock:
    """Create a mock LLM client that returns predefined JSON responses."""
    mock = MagicMock(spec=LLMClient)
    mock.router = MagicMock()
    mock.router.route.return_value = ModelConfig(model="claude-sonnet-4-20250514", max_tokens=4096)

    call_count = 0
    usage = StageUsage(stage="test", model="claude-sonnet-4-20250514", input_tokens=100, output_tokens=50)

    async def mock_complete_structured(prompt, model_cls, task_name, stage_label, model_config=None):
        nonlocal call_count
        import json
        data = json.loads(responses[call_count])
        call_count += 1
        return model_cls.model_validate(data), usage

    mock.complete_structured = mock_complete_structured
    return mock


def _make_metadata(filing_type: str) -> FilingMetadata:
    return FilingMetadata(
        filing_type=filing_type,
        company_name="Apple Inc.",
        ticker="AAPL",
        cik="0000320193",
        filing_date=date(2024, 11, 1),
        period_of_report="September 28, 2024",
    )


@pytest.mark.asyncio
async def test_ten_k_analyzer(sample_10k_filing: RawFiling):
    mock_llm = _make_mock_llm([
        MOCK_10K_ANALYSIS_JSON,
        MOCK_10K_RISKS_JSON,
        MOCK_10K_FINANCIALS_JSON,
    ])
    metadata = _make_metadata("10-K")
    analyzer = TenKAnalyzer()
    report = await analyzer.analyze(sample_10k_filing, metadata, mock_llm)

    assert report.ticker == "AAPL"
    assert report.filing_type == "10-K"
    assert "394.3B" in report.summary
    assert report.risk_factors is not None
    assert len(report.risk_factors) == 5
    assert report.financial_highlights is not None
    assert report.financial_highlights.revenue == "$394.3B"
    assert report.management_discussion is not None
    assert report.forward_looking is not None


@pytest.mark.asyncio
async def test_ten_q_analyzer(sample_10q_filing: RawFiling):
    mock_llm = _make_mock_llm([
        MOCK_10Q_ANALYSIS_JSON,
        MOCK_10Q_FINANCIALS_JSON,
    ])
    metadata = _make_metadata("10-Q")
    analyzer = TenQAnalyzer()
    report = await analyzer.analyze(sample_10q_filing, metadata, mock_llm)

    assert report.ticker == "AAPL"
    assert report.filing_type == "10-Q"
    assert "85.8B" in report.summary
    assert report.financial_highlights is not None
    assert report.financial_highlights.revenue == "$85.8B"


@pytest.mark.asyncio
async def test_eight_k_analyzer(sample_8k_filing: RawFiling):
    mock_llm = _make_mock_llm([
        MOCK_8K_ANALYSIS_JSON,
        MOCK_8K_FINANCIALS_JSON,
    ])
    metadata = _make_metadata("8-K")
    analyzer = EightKAnalyzer()
    report = await analyzer.analyze(sample_8k_filing, metadata, mock_llm)

    assert report.ticker == "AAPL"
    assert report.filing_type == "8-K"
    assert "94.9B" in report.summary
    assert report.key_events is not None
    assert len(report.key_events) == 1
    assert report.key_events[0].event_type == "earnings"
