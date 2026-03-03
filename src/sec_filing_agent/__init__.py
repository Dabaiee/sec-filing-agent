"""SEC Filing Intelligence Agent — AI-powered SEC filing analysis."""

from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.models.filing import RawFiling

__all__ = [
    "Agent",
    "AnalysisReport",
    "RawFiling",
    "analyze",
    "fetch_filing",
]
__version__ = "0.3.0"


def Agent(model: str | None = None, api_key: str | None = None):
    """Create an Agent instance for programmatic SEC filing analysis.

    Args:
        model: Optional model override (e.g., "claude-sonnet-4-20250514").
        api_key: Optional Anthropic API key. Uses ANTHROPIC_API_KEY env var if not set.

    Returns:
        Agent instance with analyze, analyze_batch, diff, compare methods.
    """
    from sec_filing_agent.agent import Agent as _Agent
    return _Agent(model=model, api_key=api_key)


async def analyze(ticker: str, filing_type: str | None = None, output_format: str = "terminal") -> AnalysisReport:
    """Analyze the latest SEC filing for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        filing_type: Optional filing type filter ("10-K", "10-Q", "8-K").
        output_format: Output format ("terminal", "json", "markdown").

    Returns:
        AnalysisReport with structured analysis results.
    """
    from sec_filing_agent.cli import run_pipeline
    return await run_pipeline(ticker, filing_type=filing_type, output_format=output_format)


async def fetch_filing(ticker: str, filing_type: str | None = None) -> RawFiling:
    """Fetch the latest SEC filing for a given ticker.

    Args:
        ticker: Stock ticker symbol (e.g., "AAPL").
        filing_type: Optional filing type filter ("10-K", "10-Q", "8-K").

    Returns:
        RawFiling with the filing content and metadata.
    """
    from sec_filing_agent.fetcher import fetch_latest_filing
    return await fetch_latest_filing(ticker, filing_type=filing_type)
