"""Polling monitor for new filings — check watched tickers and auto-analyze."""

from __future__ import annotations

import asyncio
import logging

from rich.console import Console

from sec_filing_agent.watch.alerts import send_alert
from sec_filing_agent.watch.store import WatchStore

console = Console()
logger = logging.getLogger(__name__)


class Monitor:
    """Monitor watched tickers for new filings and auto-analyze."""

    def __init__(
        self,
        store: WatchStore | None = None,
        interval_minutes: int = 60,
        webhook_url: str | None = None,
    ) -> None:
        self.store = store or WatchStore()
        self.interval_minutes = interval_minutes
        self.webhook_url = webhook_url

    async def check_ticker(self, ticker: str) -> bool:
        """Check a single ticker for new filings. Returns True if new filing found."""
        from sec_filing_agent.cli import run_pipeline
        from sec_filing_agent.fetcher import fetch_latest_filing
        from sec_filing_agent.models.config import Settings

        settings = Settings.from_env()

        try:
            filing = await fetch_latest_filing(ticker, settings=settings)
        except Exception as e:
            logger.warning("Failed to fetch filing for %s: %s", ticker, e)
            self.store.update_last_checked(ticker)
            return False

        # Check if we've already analyzed this filing
        if self.store.has_been_analyzed(filing.accession_number):
            self.store.update_last_checked(ticker)
            return False

        # New filing found — analyze it
        console.print(f"\n[bold green]New filing detected:[/bold green] {ticker} {filing.filing_type} ({filing.filing_date})")

        try:
            report = await run_pipeline(ticker, output_format="json")
            report_json = report.model_dump_json()

            self.store.save_analysis(
                ticker=ticker,
                filing_type=filing.filing_type,
                filing_date=str(filing.filing_date),
                accession=filing.accession_number,
                report_json=report_json,
            )
            self.store.update_last_checked(
                ticker,
                filing_date=str(filing.filing_date),
                accession=filing.accession_number,
            )

            # Send alert if webhook configured
            if self.webhook_url:
                await send_alert(
                    webhook_url=self.webhook_url,
                    ticker=ticker,
                    filing_type=filing.filing_type,
                    filing_date=str(filing.filing_date),
                    summary=report.summary,
                )

            console.print("  [green]Analyzed and saved.[/green]")
            return True

        except Exception as e:
            logger.error("Failed to analyze %s: %s", ticker, e)
            console.print(f"  [red]Analysis failed: {e}[/red]")
            return False

    async def check_all(self) -> int:
        """Check all watched tickers. Returns count of new filings found."""
        tickers = self.store.list_tickers()
        if not tickers:
            console.print("[dim]Watchlist is empty.[/dim]")
            return 0

        console.print(f"[bold]Checking {len(tickers)} ticker(s) for new filings...[/bold]")
        new_count = 0
        for t in tickers:
            ticker = t["ticker"]
            console.print(f"  Checking {ticker}...", end=" ")
            found = await self.check_ticker(ticker)
            if found:
                new_count += 1
            else:
                console.print("[dim]no new filings[/dim]")
        return new_count

    async def run_loop(self) -> None:
        """Run the monitoring loop indefinitely."""
        console.print(
            f"[bold cyan]Starting watchlist monitor[/bold cyan] "
            f"(checking every {self.interval_minutes} minutes)"
        )
        console.print("Press Ctrl+C to stop.\n")

        while True:
            new_count = await self.check_all()
            if new_count > 0:
                console.print(f"\n[green]Found {new_count} new filing(s).[/green]")
            else:
                console.print(f"\n[dim]No new filings. Next check in {self.interval_minutes} minutes.[/dim]")
            await asyncio.sleep(self.interval_minutes * 60)

    def generate_report(self) -> None:
        """Generate a summary report of all latest analyses."""
        from sec_filing_agent.models.analysis import AnalysisReport

        tickers = self.store.list_tickers()
        if not tickers:
            console.print("[dim]No tickers in watchlist.[/dim]")
            return

        console.print("[bold]Watchlist Report[/bold]\n")

        for t in tickers:
            ticker = t["ticker"]
            analysis = self.store.get_latest_analysis(ticker)
            if analysis:
                report = AnalysisReport.model_validate(analysis["report"])
                console.print(f"[bold]{ticker}[/bold] — {report.company_name}")
                console.print(f"  {report.filing_type} | {report.filing_date}")
                console.print(f"  {report.summary[:150]}...")
                console.print()
            else:
                console.print(f"[bold]{ticker}[/bold] — [dim]No analyses yet[/dim]")
                console.print()
