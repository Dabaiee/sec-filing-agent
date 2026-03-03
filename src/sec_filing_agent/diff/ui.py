"""Rich terminal UI for diff and comparison reports."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sec_filing_agent.diff.models import ComparisonReport, DiffReport

console = Console()


def render_diff_report(report: DiffReport) -> None:
    """Render a diff report in the terminal using Rich."""
    sections: list[str] = []

    # Header
    sections.append(
        f"[bold]{report.ticker}[/bold] — {report.company_name}\n"
        f"{report.filing_type}: {report.from_date} vs {report.to_date}"
    )

    # Summary
    sections.append(f"\n[bold]Summary:[/bold]\n{report.diff.summary}")

    # Risk Changes
    if report.diff.risk_changes:
        lines = ["[bold]Risk Factor Changes:[/bold]"]
        for rc in report.diff.risk_changes:
            if rc.change_type == "added":
                icon = "[green]+ NEW[/green]"
            elif rc.change_type == "removed":
                icon = "[red]- REMOVED[/red]"
            else:
                old = rc.old_severity.upper() if rc.old_severity else "?"
                new = rc.new_severity.upper() if rc.new_severity else "?"
                icon = f"[yellow]~ CHANGED[/yellow] {old} -> {new}"
            lines.append(f"  {icon}: {rc.title}")
            lines.append(f"    {rc.description}")
        sections.append("\n".join(lines))

    # Financial Changes
    if report.diff.financial_changes:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("Metric")
        table.add_column(report.from_date)
        table.add_column(report.to_date)
        table.add_column("Change")
        for fc in report.diff.financial_changes:
            table.add_row(
                fc.metric,
                fc.old_value or "—",
                fc.new_value or "—",
                fc.change or "—",
            )
        console.print()
        console.print("[bold]Financial Changes:[/bold]")
        console.print(table)

    # Notable Changes
    if report.diff.notable_changes:
        lines = ["[bold]Other Notable Changes:[/bold]"]
        for change in report.diff.notable_changes:
            lines.append(f"  - {change}")
        sections.append("\n".join(lines))

    # Usage
    sections.append(
        f"\n[dim]Tokens: {report.total_tokens:,} | "
        f"Cost: ${report.estimated_cost_usd:.3f}[/dim]"
    )

    body = "\n\n".join(sections)
    console.print()
    console.print(
        Panel(body, title=f"{report.ticker} {report.filing_type} Diff", border_style="yellow")
    )


def render_comparison_report(report: ComparisonReport) -> None:
    """Render a comparison report in the terminal using Rich."""
    sections: list[str] = []

    # Header
    sections.append(
        f"[bold]{report.ticker_a}[/bold] ({report.company_a}) vs "
        f"[bold]{report.ticker_b}[/bold] ({report.company_b})\n"
        f"Filing type: {report.filing_type}"
    )

    # Summary
    sections.append(f"\n[bold]Comparative Summary:[/bold]\n{report.comparison.summary}")

    # Risk Comparison
    if report.comparison.risk_comparison:
        lines = ["[bold]Risk Profile Differences:[/bold]"]
        for diff in report.comparison.risk_comparison:
            lines.append(f"  - {diff}")
        sections.append("\n".join(lines))

    # Financial Comparison
    if report.comparison.financial_comparison:
        table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
        table.add_column("Metric")
        table.add_column(report.ticker_a)
        table.add_column(report.ticker_b)
        table.add_column("Note")
        for fc in report.comparison.financial_comparison:
            table.add_row(
                fc.metric,
                fc.old_value or "—",
                fc.new_value or "—",
                fc.change or "—",
            )
        console.print()
        console.print("[bold]Financial Comparison:[/bold]")
        console.print(table)

    # Strengths
    if report.comparison.strengths_a:
        lines = [f"[bold]{report.ticker_a} Strengths:[/bold]"]
        for s in report.comparison.strengths_a:
            lines.append(f"  [green]+[/green] {s}")
        sections.append("\n".join(lines))

    if report.comparison.strengths_b:
        lines = [f"[bold]{report.ticker_b} Strengths:[/bold]"]
        for s in report.comparison.strengths_b:
            lines.append(f"  [green]+[/green] {s}")
        sections.append("\n".join(lines))

    # Usage
    sections.append(
        f"\n[dim]Tokens: {report.total_tokens:,} | "
        f"Cost: ${report.estimated_cost_usd:.3f}[/dim]"
    )

    body = "\n\n".join(sections)
    console.print()
    console.print(
        Panel(
            body,
            title=f"{report.ticker_a} vs {report.ticker_b}",
            border_style="cyan",
        )
    )
