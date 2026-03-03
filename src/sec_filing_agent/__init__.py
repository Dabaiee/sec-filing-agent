"""SEC Filing Intelligence Agent — AI-powered SEC filing analysis."""

from sec_filing_agent.models.analysis import AnalysisReport
from sec_filing_agent.models.filing import RawFiling

__all__ = ["analyze", "fetch_filing", "AnalysisReport", "RawFiling"]
__version__ = "0.1.0"


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
