"""LLM client abstraction for Claude API calls with structured output."""

from __future__ import annotations

import json
import logging
from typing import Any, TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from sec_filing_agent.llm.model_router import ModelConfig, ModelRouter
from sec_filing_agent.models.analysis import StageUsage
from sec_filing_agent.models.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """Error raised by LLM client operations."""


class LLMClient:
    """Anthropic Claude API client with structured output validation."""

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        if not self.settings.anthropic_api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY not set. Please set the environment variable."
            )
        self._client = anthropic.Anthropic(api_key=self.settings.anthropic_api_key)
        self.router = ModelRouter(settings=self.settings)
        self._usage_log: list[StageUsage] = []

    @property
    def usage_log(self) -> list[StageUsage]:
        """Get the accumulated usage log for all API calls."""
        return self._usage_log

    def clear_usage(self) -> None:
        """Clear the accumulated usage log."""
        self._usage_log.clear()

    async def complete(
        self,
        prompt: str,
        task_name: str,
        stage_label: str,
        model_config: ModelConfig | None = None,
    ) -> tuple[str, StageUsage]:
        """Send a prompt to the LLM and return the raw text response.

        Args:
            prompt: The formatted prompt string.
            task_name: Task name for model routing.
            stage_label: Human-readable label for usage tracking.
            model_config: Optional model config override.

        Returns:
            Tuple of (response_text, stage_usage).
        """
        if model_config is None:
            model_config = self.router.route(task_name)

        message = self._client.messages.create(
            model=model_config.model,
            max_tokens=model_config.max_tokens,
            messages=[{"role": "user", "content": prompt}],
        )

        response_text = message.content[0].text
        usage = StageUsage(
            stage=stage_label,
            model=model_config.model,
            input_tokens=message.usage.input_tokens,
            output_tokens=message.usage.output_tokens,
        )
        self._usage_log.append(usage)
        return response_text, usage

    async def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        task_name: str,
        stage_label: str,
        model_config: ModelConfig | None = None,
    ) -> tuple[T, StageUsage]:
        """Send a prompt and parse the response into a Pydantic model.

        Retries once on validation failure with error context.

        Args:
            prompt: The formatted prompt string.
            response_model: Pydantic model class for response validation.
            task_name: Task name for model routing.
            stage_label: Human-readable label for usage tracking.
            model_config: Optional model config override.

        Returns:
            Tuple of (parsed_model, stage_usage).

        Raises:
            LLMError: If response cannot be parsed after retry.
        """
        response_text, usage = await self.complete(
            prompt, task_name, stage_label, model_config
        )

        try:
            parsed = _parse_json_response(response_text, response_model)
            return parsed, usage
        except (json.JSONDecodeError, ValidationError) as first_error:
            logger.warning(
                "First parse attempt failed for %s: %s. Retrying with error context.",
                stage_label, first_error,
            )
            # Retry with error context
            retry_prompt = (
                f"{prompt}\n\n"
                f"IMPORTANT: Your previous response could not be parsed. "
                f"Error: {first_error}\n"
                f"Please respond with ONLY valid JSON matching the schema. "
                f"Do not include markdown code fences or any other text."
            )
            response_text, retry_usage = await self.complete(
                retry_prompt, task_name, f"{stage_label} (retry)", model_config
            )
            # Merge token counts
            usage = StageUsage(
                stage=stage_label,
                model=usage.model,
                input_tokens=usage.input_tokens + retry_usage.input_tokens,
                output_tokens=usage.output_tokens + retry_usage.output_tokens,
            )
            # Remove the retry entry, keep only the merged one
            self._usage_log.pop()
            self._usage_log[-1] = usage

            try:
                parsed = _parse_json_response(response_text, response_model)
                return parsed, usage
            except (json.JSONDecodeError, ValidationError) as second_error:
                raise LLMError(
                    f"Failed to parse LLM response for {stage_label} after retry: {second_error}"
                ) from second_error


def _parse_json_response(text: str, model: type[T]) -> T:
    """Parse a JSON response from LLM output, handling markdown fences."""
    # Strip markdown code fences if present
    text = text.strip()
    if text.startswith("```"):
        lines = text.split("\n")
        # Remove first and last lines (```json and ```)
        lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        text = "\n".join(lines)

    data = json.loads(text)
    return model.model_validate(data)


def _extract_json_from_text(text: str) -> str:
    """Try to extract JSON from text that may contain non-JSON content."""
    # Find the first { and last }
    start = text.find("{")
    end = text.rfind("}")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    # Try array
    start = text.find("[")
    end = text.rfind("]")
    if start != -1 and end != -1 and end > start:
        return text[start : end + 1]
    return text
