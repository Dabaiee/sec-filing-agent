"""Route filings to the correct analyzer based on filing type.

Uses a registry pattern — custom analyzers can be registered at runtime:

    from sec_filing_agent.router import register_analyzer
    register_analyzer("20-F", My20FAnalyzer)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sec_filing_agent.analyzers.base import BaseAnalyzer

logger = logging.getLogger(__name__)

# Global analyzer registry — maps filing type (uppercase) to analyzer class
_ANALYZER_REGISTRY: dict[str, type[BaseAnalyzer]] = {}


class RouterError(Exception):
    """Error raised when no analyzer is found for a filing type."""


def _ensure_defaults_registered() -> None:
    """Register default analyzers on first access (lazy import to avoid circular deps)."""
    if _ANALYZER_REGISTRY:
        return

    from sec_filing_agent.analyzers.eight_k import EightKAnalyzer
    from sec_filing_agent.analyzers.ten_k import TenKAnalyzer
    from sec_filing_agent.analyzers.ten_q import TenQAnalyzer

    _ANALYZER_REGISTRY["10-K"] = TenKAnalyzer
    _ANALYZER_REGISTRY["10-Q"] = TenQAnalyzer
    _ANALYZER_REGISTRY["8-K"] = EightKAnalyzer


def register_analyzer(filing_type: str, analyzer_cls: type[BaseAnalyzer]) -> None:
    """Register a custom analyzer for a filing type.

    This enables plugin-style extensibility — third-party code can register
    analyzers for new filing types (e.g., 20-F, S-1, DEF 14A) without
    modifying the core package.

    Args:
        filing_type: Filing type string (e.g., "20-F"). Will be uppercased.
        analyzer_cls: Analyzer class (must subclass BaseAnalyzer).

    Example:
        >>> from sec_filing_agent.router import register_analyzer
        >>> register_analyzer("20-F", My20FAnalyzer)
    """
    _ensure_defaults_registered()
    key = filing_type.upper().strip()
    _ANALYZER_REGISTRY[key] = analyzer_cls
    logger.info("Registered analyzer for %s: %s", key, analyzer_cls.__name__)


def get_analyzer(filing_type: str) -> BaseAnalyzer:
    """Get the appropriate analyzer for a filing type.

    Looks up the analyzer in the registry. Built-in analyzers (10-K, 10-Q, 8-K)
    are registered automatically. Custom analyzers can be added via
    ``register_analyzer()``.

    Args:
        filing_type: The filing type string (e.g., "10-K", "10-Q", "8-K").

    Returns:
        An instance of the appropriate analyzer.

    Raises:
        RouterError: If no analyzer exists for the filing type.
    """
    _ensure_defaults_registered()

    filing_type_upper = filing_type.upper().strip()
    analyzer_cls = _ANALYZER_REGISTRY.get(filing_type_upper)
    if analyzer_cls is None:
        raise RouterError(
            f"No analyzer available for filing type '{filing_type}'. "
            f"Supported types: {', '.join(sorted(_ANALYZER_REGISTRY.keys()))}"
        )
    return analyzer_cls()


def list_supported_types() -> list[str]:
    """List all registered filing types.

    Returns:
        Sorted list of supported filing type strings.
    """
    _ensure_defaults_registered()
    return sorted(_ANALYZER_REGISTRY.keys())
