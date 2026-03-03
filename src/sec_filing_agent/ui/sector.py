"""Rich terminal UI for sector peer comparison reports."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sec_filing_agent.models.sector import SectorReport

console = Console()


def render_sector_report(report: SectorReport) -> None:
    """Render a sector report in the terminal using Rich."""
    sections: list[str] = []

    # Header
    sections.append(
        f"[bold]{report.ticker}[/bold] — {report.company_name}\n"
        f"Sector: {report.sector} | Peers: {len(report.peers)} companies"
    )

    # Peer comparison table
    if report.peers:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("Ticker")
        table.add_column("Company")
        table.add_column("Revenue")
        table.add_column("Net Income")
        table.add_column("Gross Margin")
        table.add_column("Op. Margin")

        for p in report.peers:
            is_target = p.ticker == report.ticker
            style = "bold" if is_target else ""
            table.add_row(
                f"[{style}]{p.ticker}[/{style}]" if style else p.ticker,
                p.company_name[:20],
                p.revenue or "—",
                p.net_income or "—",
                p.gross_margin or "—",
                p.operating_margin or "—",
            )

        console.print()
        console.print("[bold]Peer Comparison:[/bold]")
        console.print(table)

    # Narrative
    if report.narrative:
        sections.append(f"\n[bold]Competitive Positioning:[/bold]\n{report.narrative}")

    # Usage
    if report.model_usage.stages:
        total_tokens = report.model_usage.total_input_tokens + report.model_usage.total_output_tokens
        sections.append(
            f"\n[dim]Tokens: {total_tokens:,} | "
            f"Cost: ${report.model_usage.estimated_cost_usd:.3f}[/dim]"
        )

    body = "\n".join(sections)
    console.print()
    console.print(
        Panel(body, title=f"{report.ticker} — Sector Analysis", border_style="magenta")
    )
