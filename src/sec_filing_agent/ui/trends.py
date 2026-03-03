"""Rich terminal UI for financial trend reports."""

from __future__ import annotations

from rich.console import Console
from rich.panel import Panel

from sec_filing_agent.models.trends import TrendReport

console = Console()


def render_trend_report(report: TrendReport) -> None:
    """Render a trend report in the terminal using Rich."""
    sections: list[str] = []

    # Header
    sections.append(
        f"[bold]{report.ticker}[/bold] — {report.company_name}\n"
        f"{report.years}-Year Financial Trends"
    )

    # Metrics with ASCII bar charts
    for metric in report.metrics:
        if not metric.data_points:
            continue

        lines = [f"\n[bold]{metric.name}[/bold] ({metric.unit})"]
        max_val = max(abs(d.value) for d in metric.data_points) if metric.data_points else 1
        bar_width = 30

        for dp in metric.data_points:
            bar_len = int((abs(dp.value) / max_val) * bar_width) if max_val > 0 else 0
            bar = "█" * bar_len
            lines.append(f"  {dp.year}: {dp.formatted:<12} [green]{bar}[/green]")

        if metric.cagr is not None:
            direction_icon = {"up": "↑", "down": "↓", "flat": "→", "volatile": "↕"}.get(
                metric.trend_direction, "→"
            )
            lines.append(f"  {direction_icon} CAGR: {metric.cagr:+.1f}%")

        sections.append("\n".join(lines))

    # Narrative
    if report.narrative:
        sections.append(f"\n[bold]AI Analysis:[/bold]\n{report.narrative}")

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
        Panel(body, title=f"{report.ticker} — Financial Trends", border_style="blue")
    )
