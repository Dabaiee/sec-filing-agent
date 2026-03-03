"""Model routing: send complex tasks to Sonnet, simple tasks to Haiku."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from sec_filing_agent.models.config import Settings


class TaskComplexity(Enum):
    HIGH = "high"
    LOW = "low"


@dataclass
class ModelConfig:
    model: str
    max_tokens: int


# Cost per 1M tokens (approximate, for cost tracking)
MODEL_COSTS: dict[str, dict[str, float]] = {
    "claude-sonnet-4-20250514": {"input": 3.0, "output": 15.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.00},
}

# Default model assignments
SONNET_MODEL = "claude-sonnet-4-20250514"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

# Task-to-complexity mapping
TASK_COMPLEXITY: dict[str, TaskComplexity] = {
    # HIGH complexity: reasoning, analysis, correlation
    "risk_factor_analysis": TaskComplexity.HIGH,
    "financial_trend_reasoning": TaskComplexity.HIGH,
    "forward_looking_assessment": TaskComplexity.HIGH,
    "ten_k_analysis": TaskComplexity.HIGH,
    "ten_q_analysis": TaskComplexity.HIGH,
    "eight_k_analysis": TaskComplexity.HIGH,
    # LOW complexity: classification, extraction, summarization
    "filing_classification": TaskComplexity.LOW,
    "entity_extraction": TaskComplexity.LOW,
    "section_identification": TaskComplexity.LOW,
    "financial_extraction": TaskComplexity.LOW,
    "basic_summarization": TaskComplexity.LOW,
}


@dataclass
class ModelRouter:
    """Route LLM tasks to the appropriate model tier based on complexity."""

    settings: Settings = field(default_factory=Settings.from_env)

    def route(self, task_name: str) -> ModelConfig:
        """Get the model config for a given task.

        Args:
            task_name: Name of the task (must be in TASK_COMPLEXITY).

        Returns:
            ModelConfig with the model ID and max_tokens.
        """
        # Allow env var override for all tasks
        if self.settings.sec_agent_model:
            return ModelConfig(model=self.settings.sec_agent_model, max_tokens=4096)

        complexity = TASK_COMPLEXITY.get(task_name, TaskComplexity.LOW)
        if complexity == TaskComplexity.HIGH:
            return ModelConfig(model=SONNET_MODEL, max_tokens=4096)
        else:
            return ModelConfig(model=HAIKU_MODEL, max_tokens=2048)

    @staticmethod
    def estimate_cost(model: str, input_tokens: int, output_tokens: int) -> float:
        """Estimate cost in USD for a given model and token counts."""
        costs = MODEL_COSTS.get(model, {"input": 3.0, "output": 15.0})
        input_cost = (input_tokens / 1_000_000) * costs["input"]
        output_cost = (output_tokens / 1_000_000) * costs["output"]
        return round(input_cost + output_cost, 6)
