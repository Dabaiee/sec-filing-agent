"""Route filings to the correct analyzer based on filing type."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from sec_filing_agent.analyzers.base import BaseAnalyzer


class RouterError(Exception):
    """Error raised when no analyzer is found for a filing type."""


def get_analyzer(filing_type: str) -> BaseAnalyzer:
    """Get the appropriate analyzer for a filing type.

    Args:
        filing_type: The filing type string (e.g., "10-K", "10-Q", "8-K").

    Returns:
        An instance of the appropriate analyzer.

    Raises:
        RouterError: If no analyzer exists for the filing type.
    """
    # Import here to avoid circular imports
    from sec_filing_agent.analyzers.eight_k import EightKAnalyzer
    from sec_filing_agent.analyzers.ten_k import TenKAnalyzer
    from sec_filing_agent.analyzers.ten_q import TenQAnalyzer

    analyzers: dict[str, type[BaseAnalyzer]] = {
        "10-K": TenKAnalyzer,
        "10-Q": TenQAnalyzer,
        "8-K": EightKAnalyzer,
    }

    filing_type_upper = filing_type.upper().strip()
    analyzer_cls = analyzers.get(filing_type_upper)
    if analyzer_cls is None:
        raise RouterError(
            f"No analyzer available for filing type '{filing_type}'. "
            f"Supported types: {', '.join(analyzers.keys())}"
        )
    return analyzer_cls()
