"""LLM client abstraction for Claude API calls with structured output."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TypeVar

import anthropic
from pydantic import BaseModel, ValidationError

from sec_filing_agent.llm.model_router import ModelConfig, ModelRouter
from sec_filing_agent.models.analysis import StageUsage
from sec_filing_agent.models.config import Settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

# Retry configuration for API calls
MAX_API_RETRIES = 3
INITIAL_BACKOFF_S = 1.0
MAX_BACKOFF_S = 30.0


class LLMError(Exception):
    """Error raised by LLM client operations."""


class LLMClient:
    """Anthropic Claude API client with structured output validation.

    Features:
    - Automatic model routing based on task complexity
    - Structured output parsing with Pydantic validation
    - Retry with exponential backoff for transient API errors
    - Retry with error context for JSON parse failures
    - Token usage tracking and cost estimation
    """

    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or Settings.from_env()
        if not self.settings.anthropic_api_key:
            raise LLMError(
                "ANTHROPIC_API_KEY not set. Please set the environment variable.\n"
                "  export ANTHROPIC_API_KEY=sk-ant-..."
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

        Retries with exponential backoff on transient API errors (rate limits,
        server errors). Non-retriable errors (auth, validation) fail immediately.

        Args:
            prompt: The formatted prompt string.
            task_name: Task name for model routing.
            stage_label: Human-readable label for usage tracking.
            model_config: Optional model config override.

        Returns:
            Tuple of (response_text, stage_usage).

        Raises:
            LLMError: If the API call fails after all retries.
        """
        if model_config is None:
            model_config = self.router.route(task_name)

        last_error: Exception | None = None
        backoff = INITIAL_BACKOFF_S

        for attempt in range(MAX_API_RETRIES):
            try:
                message = self._client.messages.create(
                    model=model_config.model,
                    max_tokens=model_config.max_tokens,
                    messages=[{"role": "user", "content": prompt}],
                )

                first_block = message.content[0]
                response_text = first_block.text if hasattr(first_block, "text") else str(first_block)
                usage = StageUsage(
                    stage=stage_label,
                    model=model_config.model,
                    input_tokens=message.usage.input_tokens,
                    output_tokens=message.usage.output_tokens,
                )
                self._usage_log.append(usage)
                return response_text, usage

            except anthropic.RateLimitError as e:
                last_error = e
                logger.warning(
                    "Rate limited on %s (attempt %d/%d). Retrying in %.1fs...",
                    stage_label, attempt + 1, MAX_API_RETRIES, backoff,
                )
            except anthropic.InternalServerError as e:
                last_error = e
                logger.warning(
                    "Server error on %s (attempt %d/%d). Retrying in %.1fs...",
                    stage_label, attempt + 1, MAX_API_RETRIES, backoff,
                )
            except anthropic.APIConnectionError as e:
                last_error = e
                logger.warning(
                    "Connection error on %s (attempt %d/%d). Retrying in %.1fs...",
                    stage_label, attempt + 1, MAX_API_RETRIES, backoff,
                )
            except anthropic.AuthenticationError as e:
                raise LLMError(
                    f"Authentication failed: {e}. Check your ANTHROPIC_API_KEY."
                ) from e
            except anthropic.BadRequestError as e:
                raise LLMError(
                    f"Invalid request for {stage_label}: {e}"
                ) from e

            await asyncio.sleep(backoff)
            backoff = min(backoff * 2, MAX_BACKOFF_S)

        raise LLMError(
            f"API call for {stage_label} failed after {MAX_API_RETRIES} retries: {last_error}"
        )

    async def complete_structured(
        self,
        prompt: str,
        response_model: type[T],
        task_name: str,
        stage_label: str,
        model_config: ModelConfig | None = None,
    ) -> tuple[T, StageUsage]:
        """Send a prompt and parse the response into a Pydantic model.

        Retries once on validation failure with error context appended to the
        prompt, guiding the LLM to produce valid JSON.

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
    """Parse a JSON response from LLM output, handling markdown fences.

    Handles common LLM output quirks:
    - Markdown code fences (```json ... ```)
    - Leading/trailing whitespace
    - JSON embedded in non-JSON text

    Args:
        text: Raw LLM response text.
        model: Pydantic model class for validation.

    Returns:
        Validated Pydantic model instance.

    Raises:
        json.JSONDecodeError: If JSON cannot be parsed.
        ValidationError: If parsed JSON doesn't match the model.
    """
    text = text.strip()

    # Strip markdown code fences if present
    if text.startswith("```"):
        lines = text.split("\n")
        lines = lines[1:]  # Remove opening fence
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]  # Remove closing fence
        text = "\n".join(lines)

    # Fallback: extract JSON object/array from mixed text
    if not text.startswith(("{", "[")):
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end > start:
            text = text[start : end + 1]

    data = json.loads(text)
    return model.model_validate(data)
