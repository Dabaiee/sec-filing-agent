"""Watchlist management — CRUD operations for watched tickers."""

from __future__ import annotations

from rich.console import Console
from rich.table import Table

from sec_filing_agent.watch.store import WatchStore

console = Console()


class Watchlist:
    """Manage the watchlist of tickers to monitor."""

    def __init__(self, store: WatchStore | None = None) -> None:
        self.store = store or WatchStore()

    def add(self, tickers: list[str]) -> None:
        """Add tickers to the watchlist."""
        for ticker in tickers:
            added = self.store.add_ticker(ticker)
            if added:
                console.print(f"  [green]+[/green] Added {ticker.upper()}")
            else:
                console.print(f"  [dim]Already watching {ticker.upper()}[/dim]")

    def remove(self, tickers: list[str]) -> None:
        """Remove tickers from the watchlist."""
        for ticker in tickers:
            removed = self.store.remove_ticker(ticker)
            if removed:
                console.print(f"  [red]-[/red] Removed {ticker.upper()}")
            else:
                console.print(f"  [dim]{ticker.upper()} not in watchlist[/dim]")

    def list(self) -> list[dict]:
        """List all watched tickers with their status."""
        tickers = self.store.list_tickers()
        if not tickers:
            console.print("[dim]Watchlist is empty. Add tickers with:[/dim]")
            console.print("  sec-agent watch add AAPL MSFT NVDA")
            return []

        table = Table(title="Watchlist", show_lines=False)
        table.add_column("Ticker", style="bold")
        table.add_column("Added")
        table.add_column("Last Checked")
        table.add_column("Last Filing")

        for t in tickers:
            added = t["added_at"][:10] if t["added_at"] else "—"
            checked = t["last_checked"][:10] if t["last_checked"] else "Never"
            filing = t["last_filing_date"] or "—"
            table.add_row(t["ticker"], added, checked, filing)

        console.print(table)
        return tickers
