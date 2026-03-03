"""Rich terminal UI for pipeline progress and report rendering."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from sec_filing_agent.models.analysis import AnalysisReport

console = Console()


class PipelineUI:
    """Terminal UI that shows pipeline progress with spinners and checkmarks."""

    def __init__(self, ticker: str, verbose: bool = False) -> None:
        self.ticker = ticker.upper()
        self.verbose = verbose
        self._stages: list[dict[str, Any]] = []
        self._current_status: Any = None

    def show_header(self, company_name: str) -> None:
        """Display the agent header panel."""
        console.print()
        console.print(
            Panel(
                f"[bold cyan]SEC Filing Intelligence Agent[/bold cyan]\n"
                f"Analyzing: [bold]{self.ticker}[/bold] ({company_name})",
                border_style="cyan",
            )
        )
        console.print()

    def stage_start(self, stage_name: str, model: str) -> None:
        """Called when a pipeline stage begins."""
        if model == "structured":
            model_short = "structured — no LLM"
        else:
            model_short = model.split("-")[1] if "-" in model else model
        self._stages.append({"name": stage_name, "model": model_short, "done": False})
        console.print(f"  [yellow]◐[/yellow] {stage_name}...  [dim][{model_short}][/dim]")

    def stage_complete(self, stage_name: str, duration_s: float) -> None:
        """Called when a pipeline stage completes."""
        for stage in self._stages:
            if stage["name"] == stage_name and not stage["done"]:
                stage["done"] = True
                stage["duration"] = duration_s
                break
        # Move cursor up and overwrite the line
        console.print(f"\033[1A\033[2K  [green]✓[/green] {stage_name}  [dim]{duration_s:.1f}s[/dim]")

    def show_report(self, report: AnalysisReport) -> None:
        """Render the full analysis report in a Rich panel."""
        console.print()

        sections: list[str] = []

        # Header
        sections.append(
            f"[bold]{report.ticker}[/bold] — {report.company_name}\n"
            f"{report.filing_type} | Filed: {report.filing_date}"
        )

        # Summary
        sections.append(f"\n[bold]Summary:[/bold]\n{report.summary}")

        # Risk Factors (10-K)
        if report.risk_factors:
            risk_lines = ["[bold]Top Risk Factors:[/bold]"]
            for rf in report.risk_factors:
                severity_icon = {"high": "🔴 HIGH", "medium": "🟡 MED", "low": "🟢 LOW"}.get(
                    rf.severity.lower(), rf.severity
                )
                risk_lines.append(f"  {severity_icon}: {rf.title}")
                if self.verbose:
                    risk_lines.append(f"    {rf.description}")
            sections.append("\n".join(risk_lines))

        # Financial Highlights
        if report.financial_highlights:
            fh = report.financial_highlights
            table = Table(show_header=True, header_style="bold", box=None, padding=(0, 2))
            table.add_column("Metric")
            table.add_column("Value")
            if fh.yoy_revenue_change:
                table.add_column("YoY")

            rows: list[tuple[str, ...]] = []
            if fh.revenue:
                row = ("Revenue", fh.revenue)
                if fh.yoy_revenue_change:
                    row = row + (fh.yoy_revenue_change,)
                rows.append(row)
            if fh.net_income:
                row = ("Net Income", fh.net_income)
                if fh.yoy_revenue_change:
                    row = row + ("",)
                rows.append(row)
            if fh.gross_margin:
                row = ("Gross Margin", fh.gross_margin)
                if fh.yoy_revenue_change:
                    row = row + ("",)
                rows.append(row)
            if fh.operating_margin:
                row = ("Operating Margin", fh.operating_margin)
                if fh.yoy_revenue_change:
                    row = row + ("",)
                rows.append(row)
            for key, val in fh.key_metrics.items():
                row = (key, val)
                if fh.yoy_revenue_change:
                    row = row + ("",)
                rows.append(row)

            for r in rows:
                table.add_row(*r)

            console.print()
            console.print("[bold]Financial Highlights:[/bold]")
            console.print(table)

        # Key Events (8-K)
        if report.key_events:
            event_lines = ["[bold]Key Events:[/bold]"]
            for event in report.key_events:
                impact_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(
                    event.material_impact.lower(), "●"
                )
                event_lines.append(f"  {impact_icon} [{event.event_type}] {event.headline}")
                if self.verbose:
                    event_lines.append(f"    {event.details}")
            sections.append("\n".join(event_lines))

        # Management Discussion
        if report.management_discussion:
            sections.append(
                f"[bold]Management Discussion:[/bold]\n{report.management_discussion}"
            )

        # Forward-looking statements
        if report.forward_looking:
            fl_lines = ["[bold]Forward-Looking Statements:[/bold]"]
            for stmt in report.forward_looking:
                fl_lines.append(f"  • {stmt}")
            sections.append("\n".join(fl_lines))

        # Model Usage
        usage = report.model_usage
        if usage.stages:
            usage_parts = []
            model_tokens: dict[str, int] = {}
            for stage in usage.stages:
                model_short = stage.model.split("-")[1] if "-" in stage.model else stage.model
                model_tokens[model_short] = model_tokens.get(model_short, 0) + stage.input_tokens + stage.output_tokens
            for model_name, tokens in model_tokens.items():
                usage_parts.append(f"{model_name}: {tokens:,} tokens")
            usage_str = " · ".join(usage_parts)
            cost_str = f"${usage.estimated_cost_usd:.3f}"
            sections.append(
                f"[dim]Model Usage: {usage_str}\n"
                f"Estimated cost: {cost_str}  |  "
                f"Pipeline: {report.pipeline_duration_ms}ms[/dim]"
            )

        body = "\n\n".join(sections)
        console.print(Panel(body, title="Analysis Report", border_style="green"))


def render_json(report: AnalysisReport) -> str:
    """Render the report as formatted JSON."""
    return report.model_dump_json(indent=2)


def render_markdown(report: AnalysisReport) -> str:
    """Render the report as Markdown."""
    lines = [
        f"# {report.ticker} — {report.company_name}",
        f"**{report.filing_type}** | Filed: {report.filing_date} | Period: {report.period_of_report}",
        "",
        "## Summary",
        report.summary,
        "",
    ]

    if report.risk_factors:
        lines.append("## Risk Factors")
        for rf in report.risk_factors:
            lines.append(f"- **[{rf.severity.upper()}] {rf.title}** ({rf.category}): {rf.description}")
        lines.append("")

    if report.financial_highlights:
        fh = report.financial_highlights
        lines.append("## Financial Highlights")
        lines.append("| Metric | Value |")
        lines.append("|--------|-------|")
        if fh.revenue:
            lines.append(f"| Revenue | {fh.revenue} |")
        if fh.net_income:
            lines.append(f"| Net Income | {fh.net_income} |")
        if fh.gross_margin:
            lines.append(f"| Gross Margin | {fh.gross_margin} |")
        if fh.operating_margin:
            lines.append(f"| Operating Margin | {fh.operating_margin} |")
        for key, val in fh.key_metrics.items():
            lines.append(f"| {key} | {val} |")
        lines.append("")

    if report.key_events:
        lines.append("## Key Events")
        for event in report.key_events:
            lines.append(f"- **[{event.material_impact.upper()}] {event.headline}** ({event.event_type}): {event.details}")
        lines.append("")

    if report.management_discussion:
        lines.append("## Management Discussion")
        lines.append(report.management_discussion)
        lines.append("")

    if report.forward_looking:
        lines.append("## Forward-Looking Statements")
        for stmt in report.forward_looking:
            lines.append(f"- {stmt}")
        lines.append("")

    usage = report.model_usage
    if usage.stages:
        lines.append("---")
        lines.append(
            f"*Model usage: {usage.total_input_tokens + usage.total_output_tokens:,} tokens | "
            f"Cost: ${usage.estimated_cost_usd:.3f} | "
            f"Pipeline: {report.pipeline_duration_ms}ms*"
        )

    return "\n".join(lines)
