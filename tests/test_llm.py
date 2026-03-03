"""Tests for LLM client and model router."""

from __future__ import annotations

import json

import pytest
from pydantic import BaseModel

from sec_filing_agent.llm.client import LLMClient, LLMError, _parse_json_response
from sec_filing_agent.llm.model_router import (
    HAIKU_MODEL,
    SONNET_MODEL,
    ModelRouter,
    TaskComplexity,
)
from sec_filing_agent.models.config import Settings


# ── Model Router Tests ───────────────────────────────────────────────────────


def test_route_high_complexity_to_sonnet():
    """High complexity tasks route to Sonnet."""
    settings = Settings(anthropic_api_key="test-key")
    router = ModelRouter(settings=settings)
    config = router.route("risk_factor_analysis")
    assert config.model == SONNET_MODEL
    assert config.max_tokens == 4096


def test_route_low_complexity_to_haiku():
    """Low complexity tasks route to Haiku."""
    settings = Settings(anthropic_api_key="test-key")
    router = ModelRouter(settings=settings)
    config = router.route("financial_extraction")
    assert config.model == HAIKU_MODEL
    assert config.max_tokens == 2048


def test_route_unknown_task_defaults_to_haiku():
    """Unknown tasks default to low complexity (Haiku)."""
    settings = Settings(anthropic_api_key="test-key")
    router = ModelRouter(settings=settings)
    config = router.route("unknown_task_xyz")
    assert config.model == HAIKU_MODEL


def test_route_env_override():
    """SEC_AGENT_MODEL overrides all routing."""
    settings = Settings(anthropic_api_key="test-key", sec_agent_model="custom-model-id")
    router = ModelRouter(settings=settings)
    config = router.route("risk_factor_analysis")
    assert config.model == "custom-model-id"
    assert config.max_tokens == 4096


def test_estimate_cost_sonnet():
    """Cost estimation for Sonnet model."""
    cost = ModelRouter.estimate_cost(SONNET_MODEL, 1000, 500)
    # (1000/1M)*3.0 + (500/1M)*15.0 = 0.003 + 0.0075 = 0.0105
    assert abs(cost - 0.0105) < 0.0001


def test_estimate_cost_haiku():
    """Cost estimation for Haiku model."""
    cost = ModelRouter.estimate_cost(HAIKU_MODEL, 1000, 500)
    # (1000/1M)*0.80 + (500/1M)*4.00 = 0.0008 + 0.002 = 0.0028
    assert abs(cost - 0.0028) < 0.0001


def test_estimate_cost_unknown_model():
    """Unknown model uses Sonnet pricing as default."""
    cost = ModelRouter.estimate_cost("unknown-model", 1000, 500)
    assert cost > 0


# ── JSON Parsing Tests ───────────────────────────────────────────────────────


class SampleResponse(BaseModel):
    summary: str
    score: int


def test_parse_json_response_basic():
    """Parse clean JSON response."""
    text = '{"summary": "Test summary", "score": 42}'
    result = _parse_json_response(text, SampleResponse)
    assert result.summary == "Test summary"
    assert result.score == 42


def test_parse_json_response_with_markdown_fences():
    """Parse JSON wrapped in markdown code fences."""
    text = '```json\n{"summary": "Test summary", "score": 42}\n```'
    result = _parse_json_response(text, SampleResponse)
    assert result.summary == "Test summary"
    assert result.score == 42


def test_parse_json_response_invalid_json():
    """Invalid JSON raises JSONDecodeError."""
    with pytest.raises(json.JSONDecodeError):
        _parse_json_response("not valid json", SampleResponse)


def test_parse_json_response_validation_error():
    """Missing required fields raises ValidationError."""
    from pydantic import ValidationError
    with pytest.raises(ValidationError):
        _parse_json_response('{"summary": "test"}', SampleResponse)


# ── LLM Client Tests ────────────────────────────────────────────────────────


def test_llm_client_requires_api_key():
    """LLMClient raises error if no API key."""
    settings = Settings(anthropic_api_key="")
    with pytest.raises(LLMError, match="ANTHROPIC_API_KEY"):
        LLMClient(settings=settings)


def test_llm_client_initializes_with_key():
    """LLMClient initializes successfully with API key."""
    settings = Settings(anthropic_api_key="test-key-123")
    client = LLMClient(settings=settings)
    assert client.usage_log == []
    assert client.router is not None


def test_llm_client_clear_usage():
    """Usage log can be cleared."""
    settings = Settings(anthropic_api_key="test-key-123")
    client = LLMClient(settings=settings)
    # Manually inject a usage entry
    from sec_filing_agent.models.analysis import StageUsage
    client._usage_log.append(StageUsage(stage="test", model="m", input_tokens=1, output_tokens=1))
    assert len(client.usage_log) == 1
    client.clear_usage()
    assert len(client.usage_log) == 0


# ── Task Complexity Mapping Tests ────────────────────────────────────────────


def test_all_analysis_tasks_are_high():
    """All analysis-related tasks should be high complexity."""
    from sec_filing_agent.llm.model_router import TASK_COMPLEXITY
    high_tasks = ["risk_factor_analysis", "ten_k_analysis", "ten_q_analysis", "eight_k_analysis"]
    for task in high_tasks:
        assert TASK_COMPLEXITY[task] == TaskComplexity.HIGH, f"{task} should be HIGH"


def test_all_extraction_tasks_are_low():
    """All extraction-related tasks should be low complexity."""
    from sec_filing_agent.llm.model_router import TASK_COMPLEXITY
    low_tasks = ["filing_classification", "entity_extraction", "financial_extraction"]
    for task in low_tasks:
        assert TASK_COMPLEXITY[task] == TaskComplexity.LOW, f"{task} should be LOW"


# ── Cost Tracking Tests ─────────────────────────────────────────────────────


def test_cost_tracking_accumulates():
    """Usage log accumulates across multiple stages."""
    from sec_filing_agent.models.analysis import ModelUsage, StageUsage

    settings = Settings(anthropic_api_key="test-key-123")
    client = LLMClient(settings=settings)
    # Simulate a multi-stage pipeline
    stages = [
        StageUsage(stage="risk_analysis", model=SONNET_MODEL, input_tokens=1500, output_tokens=500),
        StageUsage(stage="financial_extraction", model=HAIKU_MODEL, input_tokens=800, output_tokens=200),
        StageUsage(stage="summary", model=HAIKU_MODEL, input_tokens=600, output_tokens=300),
    ]
    for s in stages:
        client._usage_log.append(s)

    # Build ModelUsage from log
    total_in = sum(s.input_tokens for s in client.usage_log)
    total_out = sum(s.output_tokens for s in client.usage_log)
    total_cost = sum(
        ModelRouter.estimate_cost(s.model, s.input_tokens, s.output_tokens)
        for s in client.usage_log
    )
    usage = ModelUsage(
        stages=client.usage_log,
        total_input_tokens=total_in,
        total_output_tokens=total_out,
        estimated_cost_usd=total_cost,
    )
    assert usage.total_input_tokens == 2900
    assert usage.total_output_tokens == 1000
    assert usage.estimated_cost_usd > 0
    assert len(usage.stages) == 3


def test_cost_estimate_mixed_models():
    """Cost estimation correctly differentiates Sonnet vs Haiku pricing."""
    # Sonnet costs more than Haiku for the same token count
    sonnet_cost = ModelRouter.estimate_cost(SONNET_MODEL, 1000, 1000)
    haiku_cost = ModelRouter.estimate_cost(HAIKU_MODEL, 1000, 1000)
    assert sonnet_cost > haiku_cost
