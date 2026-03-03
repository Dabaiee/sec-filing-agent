"""Typer CLI for SEC Filing Intelligence Agent."""

from __future__ import annotations

import asyncio
import time

import typer
from rich.console import Console

from sec_filing_agent.models.analysis import AnalysisReport, ModelUsage
from sec_filing_agent.models.config import Settings

app = typer.Typer(
    name="sec-agent",
    help="SEC Filing Intelligence Agent — AI-powered SEC filing analysis",
    add_completion=False,
)
watch_app = typer.Typer(help="Watchlist — monitor tickers for new filings")
app.add_typer(watch_app, name="watch")
console = Console()


async def run_pipeline(
    ticker: str,
    filing_type: str | None = None,
    output_format: str = "terminal",
    model: str | None = None,
    verbose: bool = False,
) -> AnalysisReport:
    """Run the full analysis pipeline.

    Args:
        ticker: Stock ticker symbol.
        filing_type: Optional filing type filter.
        output_format: Output format (terminal, json, markdown).
        model: Optional model override.
        verbose: Show detailed logging.

    Returns:
        AnalysisReport with the analysis results.
    """
    from sec_filing_agent.classifier import classify_filing
    from sec_filing_agent.fetcher import fetch_latest_filing
    from sec_filing_agent.llm.client import LLMClient
    from sec_filing_agent.llm.model_router import ModelRouter
    from sec_filing_agent.router import get_analyzer
    from sec_filing_agent.ui.terminal import PipelineUI, render_json, render_markdown

    settings = Settings.from_env()
    if model:
        settings.sec_agent_model = model

    pipeline_start = time.monotonic()
    ui = PipelineUI(ticker, verbose=verbose)

    # Stage 1: Fetch filing
    if output_format == "terminal":
        ui.stage_start("Fetching filing from SEC EDGAR", "httpx")
    t0 = time.monotonic()

    try:
        raw_filing = await fetch_latest_filing(ticker, filing_type=filing_type, settings=settings)
    except Exception as e:
        console.print(f"[red]Error fetching filing:[/red] {e}")
        raise typer.Exit(code=1) from e

    if output_format == "terminal":
        ui.show_header(raw_filing.company_name)
        ui.stage_complete("Fetching filing from SEC EDGAR", time.monotonic() - t0)

    # Stage 2: Classify
    if output_format == "terminal":
        ui.stage_start("Classifying filing", "heuristic")
    t0 = time.monotonic()

    metadata = classify_filing(raw_filing)

    if output_format == "terminal":
        ui.stage_complete("Classifying filing", time.monotonic() - t0)

    # Stage 3: Route
    if output_format == "terminal":
        ui.stage_start(f"Routing to {metadata.filing_type} analyzer", "router")
    t0 = time.monotonic()

    analyzer = get_analyzer(metadata.filing_type)

    if output_format == "terminal":
        ui.stage_complete(f"Routing to {metadata.filing_type} analyzer", time.monotonic() - t0)

    # Stage 4: Analyze with LLM
    try:
        llm_client = LLMClient(settings=settings)
    except Exception as e:
        console.print(f"[red]Error initializing LLM client:[/red] {e}")
        raise typer.Exit(code=1) from e

    stage_start_cb = ui.stage_start if output_format == "terminal" else None
    stage_complete_cb = ui.stage_complete if output_format == "terminal" else None

    try:
        report = await analyzer.analyze(
            raw_filing,
            metadata,
            llm_client,
            on_stage_start=stage_start_cb,
            on_stage_complete=stage_complete_cb,
        )
    except Exception as e:
        console.print(f"[red]Error during analysis:[/red] {e}")
        raise typer.Exit(code=1) from e

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

    # Output
    if output_format == "json":
        console.print(render_json(report))
    elif output_format == "markdown":
        console.print(render_markdown(report))
    else:
        ui.show_report(report)

    return report


@app.command()
def analyze(
    ticker: str = typer.Argument(help="Stock ticker symbol (e.g., AAPL)"),
    filing_type: str | None = typer.Option(
        None, "--filing-type", "-t", help="Filing type: 10-K, 10-Q, 8-K"
    ),
    output: str = typer.Option(
        "terminal", "--output", "-o", help="Output format: terminal, json, markdown"
    ),
    model: str | None = typer.Option(
        None, "--model", "-m", help="Force a specific model for all stages"
    ),
    verbose: bool = typer.Option(
        False, "--verbose", "-v", help="Show detailed pipeline logging"
    ),
) -> None:
    """Analyze the latest SEC filing for a given ticker."""
    asyncio.run(
        run_pipeline(
            ticker=ticker,
            filing_type=filing_type,
            output_format=output,
            model=model,
            verbose=verbose,
        )
    )


@app.command()
def diff(
    ticker: str = typer.Argument(help="Stock ticker symbol (e.g., AAPL)"),
    filing_type: str = typer.Option(
        "10-K", "--filing-type", "-t", help="Filing type: 10-K, 10-Q, 8-K"
    ),
    from_date: str = typer.Option(
        ..., "--from", "-f", help="Earlier filing date hint (e.g., '2023')"
    ),
    to_date: str = typer.Option(
        ..., "--to", help="Later filing date hint (e.g., '2024')"
    ),
    output: str = typer.Option(
        "terminal", "--output", "-o", help="Output format: terminal, json"
    ),
) -> None:
    """Compare a company's filings across time periods."""
    async def _run() -> None:
        from sec_filing_agent.diff.analyzer import diff_filings
        from sec_filing_agent.diff.ui import render_diff_report

        try:
            report = await diff_filings(
                ticker=ticker,
                filing_type=filing_type,
                from_hint=from_date,
                to_hint=to_date,
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1) from e

        if output == "json":
            console.print(report.model_dump_json(indent=2))
        else:
            render_diff_report(report)

    asyncio.run(_run())


@app.command()
def compare(
    ticker_a: str = typer.Argument(help="First ticker symbol (e.g., AAPL)"),
    ticker_b: str = typer.Argument(help="Second ticker symbol (e.g., MSFT)"),
    filing_type: str = typer.Option(
        "10-K", "--filing-type", "-t", help="Filing type: 10-K, 10-Q, 8-K"
    ),
    output: str = typer.Option(
        "terminal", "--output", "-o", help="Output format: terminal, json"
    ),
) -> None:
    """Compare filings of two different companies."""
    async def _run() -> None:
        from sec_filing_agent.diff.analyzer import compare_companies
        from sec_filing_agent.diff.ui import render_comparison_report

        try:
            report = await compare_companies(
                ticker_a=ticker_a,
                ticker_b=ticker_b,
                filing_type=filing_type,
            )
        except Exception as e:
            console.print(f"[red]Error:[/red] {e}")
            raise typer.Exit(code=1) from e

        if output == "json":
            console.print(report.model_dump_json(indent=2))
        else:
            render_comparison_report(report)

    asyncio.run(_run())


@watch_app.command("add")
def watch_add(
    tickers: list[str] = typer.Argument(help="Ticker symbols to add"),
) -> None:
    """Add tickers to the watchlist."""
    from sec_filing_agent.watch.watchlist import Watchlist
    wl = Watchlist()
    wl.add(tickers)


@watch_app.command("remove")
def watch_remove(
    tickers: list[str] = typer.Argument(help="Ticker symbols to remove"),
) -> None:
    """Remove tickers from the watchlist."""
    from sec_filing_agent.watch.watchlist import Watchlist
    wl = Watchlist()
    wl.remove(tickers)


@watch_app.command("list")
def watch_list() -> None:
    """List all watched tickers."""
    from sec_filing_agent.watch.watchlist import Watchlist
    wl = Watchlist()
    wl.list()


@watch_app.command("start")
def watch_start(
    interval: int = typer.Option(60, "--interval", "-i", help="Check interval in minutes"),
    webhook: str | None = typer.Option(None, "--webhook", "-w", help="Webhook URL for alerts"),
) -> None:
    """Start monitoring for new filings."""
    from sec_filing_agent.watch.monitor import Monitor
    monitor = Monitor(interval_minutes=interval, webhook_url=webhook)
    asyncio.run(monitor.run_loop())


@watch_app.command("check")
def watch_check() -> None:
    """Check all watched tickers for new filings once."""
    from sec_filing_agent.watch.monitor import Monitor
    monitor = Monitor()
    asyncio.run(monitor.check_all())


@watch_app.command("report")
def watch_report() -> None:
    """Show the latest analysis for all watched tickers."""
    from sec_filing_agent.watch.monitor import Monitor
    monitor = Monitor()
    monitor.generate_report()


@app.command()
def version() -> None:
    """Show the version."""
    from sec_filing_agent import __version__
    console.print(f"sec-filing-agent v{__version__}")


def main() -> None:
    """Entry point for the CLI."""
    app()


if __name__ == "__main__":
    main()
