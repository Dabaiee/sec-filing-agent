"""Streamlit web app for SEC Filing Intelligence Agent."""

from __future__ import annotations

import asyncio
import time

import streamlit as st

st.set_page_config(
    page_title="SEC Filing Intelligence Agent",
    page_icon="📊",
    layout="wide",
)


def run_async(coro):
    """Run an async coroutine from synchronous Streamlit context."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


# ── Single Analysis helpers ──────────────────────────────────────────────────


async def run_analysis(ticker: str, filing_type: str | None, progress_cb):
    """Run the full analysis pipeline with progress callbacks for the web UI."""
    from sec_filing_agent.classifier import classify_filing
    from sec_filing_agent.fetcher import fetch_latest_filing
    from sec_filing_agent.llm.client import LLMClient
    from sec_filing_agent.llm.model_router import ModelRouter
    from sec_filing_agent.models.analysis import ModelUsage
    from sec_filing_agent.models.config import Settings
    from sec_filing_agent.router import get_analyzer

    settings = Settings.from_env()
    pipeline_start = time.monotonic()

    # Stage 1: Fetch
    progress_cb("fetch", "in_progress", "Fetching filing from SEC EDGAR...")
    raw_filing = await fetch_latest_filing(ticker, filing_type=filing_type, settings=settings)
    progress_cb(
        "fetch", "done",
        f"Fetched {raw_filing.filing_type} filing ({raw_filing.filing_date})",
    )

    # Stage 2: Classify
    progress_cb("classify", "in_progress", "Classifying filing type...")
    metadata = classify_filing(raw_filing)
    progress_cb("classify", "done", f"Classified: {metadata.filing_type}")

    # Stage 3: Route
    progress_cb("route", "in_progress", "Routing to analyzer...")
    analyzer = get_analyzer(metadata.filing_type)
    progress_cb("route", "done", f"Routed to {metadata.filing_type} Analyzer")

    # Stage 4: Analyze
    llm_client = LLMClient(settings=settings)

    def on_stage_start(name: str, model: str) -> None:
        model_short = model.split("-")[1] if "-" in model else model
        progress_cb("analyze", "in_progress", f"{name}... [{model_short}]")

    def on_stage_complete(name: str, duration: float) -> None:
        progress_cb("analyze_step", "done", f"{name} ({duration:.1f}s)")

    report = await analyzer.analyze(
        raw_filing, metadata, llm_client,
        on_stage_start=on_stage_start,
        on_stage_complete=on_stage_complete,
    )

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

    progress_cb("done", "done", "Analysis complete!")
    return report


def render_report(report):
    """Render the analysis report using Streamlit components."""
    st.markdown("---")
    st.markdown(f"## {report.ticker} — {report.company_name}")
    st.markdown(
        f"**{report.filing_type}** | Filed: {report.filing_date} "
        f"| Period: {report.period_of_report}"
    )

    # Summary
    st.markdown("### Summary")
    st.info(report.summary)

    # Risk Factors
    if report.risk_factors:
        st.markdown("### Top Risk Factors")
        for rf in report.risk_factors:
            severity_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = severity_map.get(rf.severity.lower(), "⚪")
            with st.expander(f"{icon} **{rf.severity.upper()}**: {rf.title} ({rf.category})"):
                st.write(rf.description)

    # Financial Highlights
    if report.financial_highlights:
        st.markdown("### Financial Highlights")
        fh = report.financial_highlights
        cols = st.columns(4)
        metrics = []
        if fh.revenue:
            metrics.append(("Revenue", fh.revenue, fh.yoy_revenue_change))
        if fh.net_income:
            metrics.append(("Net Income", fh.net_income, None))
        if fh.gross_margin:
            metrics.append(("Gross Margin", fh.gross_margin, None))
        if fh.operating_margin:
            metrics.append(("Operating Margin", fh.operating_margin, None))

        for i, (label, value, delta) in enumerate(metrics):
            with cols[i % 4]:
                st.metric(label=label, value=value, delta=delta)

        if fh.key_metrics:
            st.markdown("**Additional Metrics**")
            metric_cols = st.columns(min(len(fh.key_metrics), 4))
            for i, (key, val) in enumerate(fh.key_metrics.items()):
                with metric_cols[i % len(metric_cols)]:
                    st.metric(label=key, value=val)

    # Key Events (8-K)
    if report.key_events:
        st.markdown("### Key Events")
        for event in report.key_events:
            impact_map = {"high": "🔴", "medium": "🟡", "low": "🟢"}
            icon = impact_map.get(event.material_impact.lower(), "⚪")
            with st.expander(f"{icon} [{event.event_type}] {event.headline}"):
                st.write(event.details)
                st.caption(f"Material impact: {event.material_impact}")

    # Management Discussion
    if report.management_discussion:
        st.markdown("### Management Discussion")
        st.write(report.management_discussion)

    # Forward-Looking Statements
    if report.forward_looking:
        st.markdown("### Forward-Looking Statements")
        for stmt in report.forward_looking:
            st.markdown(f"- {stmt}")

    # Model Usage
    _render_usage_footer(report.model_usage, report.pipeline_duration_ms)


def _render_usage_footer(model_usage, pipeline_duration_ms: int | None = None):
    """Render model usage metrics."""
    st.markdown("---")
    st.markdown("### Model Usage")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tokens", f"{model_usage.total_input_tokens + model_usage.total_output_tokens:,}")
    with col2:
        st.metric("Estimated Cost", f"${model_usage.estimated_cost_usd:.3f}")
    with col3:
        if pipeline_duration_ms is not None:
            st.metric("Pipeline Duration", f"{pipeline_duration_ms:,}ms")
        else:
            st.metric("Stages", f"{len(model_usage.stages)}")

    if model_usage.stages:
        with st.expander("Per-stage breakdown"):
            for stage in model_usage.stages:
                model_short = stage.model.split("-")[1] if "-" in stage.model else stage.model
                st.markdown(
                    f"- **{stage.stage}** [{model_short}]: "
                    f"{stage.input_tokens:,} in / {stage.output_tokens:,} out"
                )


def get_report_json(report) -> str:
    """Get JSON export of report."""
    return report.model_dump_json(indent=2)


def get_report_markdown(report) -> str:
    """Get Markdown export of report."""
    from sec_filing_agent.ui.terminal import render_markdown
    return render_markdown(report)


# ── Trends helpers ───────────────────────────────────────────────────────────


def render_trends_chart(report):
    """Render trend report with charts using Streamlit."""
    import pandas as pd

    st.markdown(f"## {report.ticker} — {report.company_name}")
    st.markdown(f"**{report.years}-Year Financial Trends**")

    if not report.metrics:
        st.warning("No XBRL financial data available for this company.")
        return

    for metric in report.metrics:
        if not metric.data_points:
            continue

        st.markdown(f"### {metric.name} ({metric.unit})")

        # Build chart data
        chart_data = pd.DataFrame(
            {"Year": [dp.year for dp in metric.data_points],
             metric.name: [dp.value for dp in metric.data_points]}
        ).set_index("Year")

        st.bar_chart(chart_data)

        # Show data table
        table_data = pd.DataFrame(
            {"Year": [dp.year for dp in metric.data_points],
             "Value": [dp.formatted for dp in metric.data_points]}
        )
        st.dataframe(table_data, hide_index=True, use_container_width=True)

        # CAGR and direction
        if metric.cagr is not None:
            direction_icon = {"up": "↑", "down": "↓", "flat": "→", "volatile": "↕"}.get(
                metric.trend_direction, "→"
            )
            st.caption(f"{direction_icon} CAGR: {metric.cagr:+.1f}% | Trend: {metric.trend_direction}")

    # Narrative
    if report.narrative:
        st.markdown("### AI Analysis")
        st.info(report.narrative)

    # Usage
    if report.model_usage.stages:
        _render_usage_footer(report.model_usage)


# ── Sector helpers ───────────────────────────────────────────────────────────


def render_sector_streamlit(report):
    """Render sector report using Streamlit."""
    import pandas as pd

    st.markdown(f"## {report.ticker} — {report.company_name}")
    st.markdown(f"**Sector:** {report.sector} | **Peers:** {len(report.peers)} companies")

    if report.peers:
        st.markdown("### Peer Comparison")
        rows = []
        for p in report.peers:
            rows.append({
                "Ticker": p.ticker,
                "Company": p.company_name,
                "Revenue": p.revenue or "—",
                "Net Income": p.net_income or "—",
                "Gross Margin": p.gross_margin or "—",
                "Op. Margin": p.operating_margin or "—",
            })
        df = pd.DataFrame(rows)
        st.dataframe(df, hide_index=True, use_container_width=True)

    if report.narrative:
        st.markdown("### Competitive Positioning")
        st.info(report.narrative)

    if report.model_usage.stages:
        _render_usage_footer(report.model_usage)


# ── Diff / Compare helpers ───────────────────────────────────────────────────


def render_diff_streamlit(report):
    """Render a diff report using Streamlit."""
    st.markdown(f"## {report.ticker} — {report.company_name}")
    st.markdown(f"**{report.filing_type}** | {report.from_date} → {report.to_date}")

    st.markdown("### Summary")
    st.info(report.diff.summary)

    if report.diff.financial_changes:
        st.markdown("### Financial Changes")
        for fc in report.diff.financial_changes:
            cols = st.columns([2, 2, 2, 1])
            with cols[0]:
                st.write(f"**{fc.metric}**")
            with cols[1]:
                st.write(fc.old_value or "—")
            with cols[2]:
                st.write(fc.new_value or "—")
            with cols[3]:
                st.write(fc.change or "—")

    if report.diff.risk_changes:
        st.markdown("### Risk Changes")
        for rc in report.diff.risk_changes:
            icon = {"added": "🆕", "removed": "❌", "changed": "🔄"}.get(rc.change_type, "•")
            with st.expander(f"{icon} [{rc.change_type.upper()}] {rc.title}"):
                st.write(rc.description)
                if rc.old_severity and rc.new_severity:
                    st.caption(f"Severity: {rc.old_severity} → {rc.new_severity}")

    if report.diff.notable_changes:
        st.markdown("### Other Notable Changes")
        for nc in report.diff.notable_changes:
            st.markdown(f"- {nc}")

    st.caption(f"Tokens: {report.total_tokens:,} | Cost: ${report.estimated_cost_usd:.3f}")


def render_comparison_streamlit(report):
    """Render a company comparison report using Streamlit."""
    st.markdown(f"## {report.ticker_a} vs {report.ticker_b}")
    st.markdown(
        f"**{report.company_a}** vs **{report.company_b}** | "
        f"Filing type: {report.filing_type}"
    )

    st.markdown("### Summary")
    st.info(report.comparison.summary)

    if report.comparison.financial_comparison:
        st.markdown("### Financial Comparison")
        for fc in report.comparison.financial_comparison:
            cols = st.columns([2, 2, 2, 1])
            with cols[0]:
                st.write(f"**{fc.metric}**")
            with cols[1]:
                st.write(fc.old_value or "—")
            with cols[2]:
                st.write(fc.new_value or "—")
            with cols[3]:
                st.write(fc.change or "—")

    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown(f"### {report.ticker_a} Strengths")
        for s in report.comparison.strengths_a:
            st.markdown(f"- {s}")
    with col_b:
        st.markdown(f"### {report.ticker_b} Strengths")
        for s in report.comparison.strengths_b:
            st.markdown(f"- {s}")

    if report.comparison.risk_comparison:
        st.markdown("### Risk Comparison")
        for rc in report.comparison.risk_comparison:
            st.markdown(f"- {rc}")

    st.caption(f"Tokens: {report.total_tokens:,} | Cost: ${report.estimated_cost_usd:.3f}")


# ── Main App ─────────────────────────────────────────────────────────────────


st.title("📊 SEC Filing Intelligence Agent")
st.markdown(
    "AI-powered analysis of SEC filings with hybrid XBRL + LLM approach. "
    "Financial numbers from structured data. Qualitative analysis from AI."
)

# Sidebar
with st.sidebar:
    st.markdown("### Settings")
    st.caption(
        "Set `ANTHROPIC_API_KEY` environment variable before running. "
        "Uses Claude Sonnet for reasoning and Claude Haiku for extraction."
    )
    st.markdown("---")
    st.markdown(
        "**Powered by [Claude](https://anthropic.com)**  \n"
        "Built with [sec-filing-agent](https://github.com/Dabaiee/sec-filing-agent)"
    )

# Tabs
tab_analyze, tab_diff, tab_trends, tab_sector = st.tabs(
    ["Single Analysis", "Compare / Diff", "Trends", "Sector"]
)

# ── Tab: Single Analysis ─────────────────────────────────────────────────────

with tab_analyze:
    col_input, col_type, col_btn = st.columns([2, 2, 1])
    with col_input:
        ticker = st.text_input(
            "Ticker Symbol",
            placeholder="AAPL",
            max_chars=10,
            label_visibility="collapsed",
            key="analyze_ticker",
        ).strip().upper()
    with col_type:
        filing_type = st.selectbox(
            "Filing Type",
            options=["Latest Available", "10-K", "10-Q", "8-K"],
            label_visibility="collapsed",
            key="analyze_filing_type",
        )
    with col_btn:
        analyze_btn = st.button("Analyze", type="primary", use_container_width=True, key="analyze_btn")

    if analyze_btn and ticker:
        selected_type = None if filing_type == "Latest Available" else filing_type

        progress_container = st.container()
        progress_items: list[tuple[str, str, str]] = []

        def update_progress(stage_id: str, status: str, message: str) -> None:
            progress_items.append((stage_id, status, message))

        with st.spinner("Running analysis pipeline..."):
            try:
                report = run_async(run_analysis(ticker, selected_type, update_progress))
            except Exception as e:
                st.error(f"Analysis failed: {e}")
                st.stop()

        with progress_container:
            st.markdown("#### Pipeline Progress")
            for _stage_id, status, message in progress_items:
                if status == "done":
                    st.markdown(f"✅ {message}")
                else:
                    st.markdown(f"🔄 {message}")

        render_report(report)

        st.markdown("---")
        dl_col1, dl_col2 = st.columns(2)
        with dl_col1:
            st.download_button(
                "📥 Download JSON",
                data=get_report_json(report),
                file_name=f"{report.ticker}_{report.filing_type}_{report.filing_date}.json",
                mime="application/json",
                use_container_width=True,
            )
        with dl_col2:
            st.download_button(
                "📥 Download Markdown",
                data=get_report_markdown(report),
                file_name=f"{report.ticker}_{report.filing_type}_{report.filing_date}.md",
                mime="text/markdown",
                use_container_width=True,
            )

    elif analyze_btn and not ticker:
        st.warning("Please enter a ticker symbol.")

# ── Tab: Compare / Diff ──────────────────────────────────────────────────────

with tab_diff:
    diff_mode = st.radio(
        "Mode",
        options=["Time Diff (same company)", "Company Comparison"],
        horizontal=True,
        key="diff_mode",
    )

    if diff_mode == "Time Diff (same company)":
        st.markdown("Compare the same company's filings across two time periods.")
        col1, col2 = st.columns(2)
        with col1:
            diff_ticker = st.text_input("Ticker", placeholder="AAPL", key="diff_ticker").strip().upper()
            diff_filing_type = st.selectbox(
                "Filing Type", options=["10-K", "10-Q", "8-K"], key="diff_filing_type"
            )
        with col2:
            diff_from = st.text_input("From (year or date)", placeholder="2023", key="diff_from")
            diff_to = st.text_input("To (year or date)", placeholder="2024", key="diff_to")

        diff_btn = st.button("Compare Periods", type="primary", key="diff_btn")

        if diff_btn and diff_ticker and diff_from and diff_to:
            with st.spinner("Analyzing filing differences..."):
                try:
                    from sec_filing_agent.diff.analyzer import diff_filings
                    report = run_async(diff_filings(
                        ticker=diff_ticker,
                        filing_type=diff_filing_type,
                        from_hint=diff_from,
                        to_hint=diff_to,
                    ))
                except Exception as e:
                    st.error(f"Diff analysis failed: {e}")
                    st.stop()
            render_diff_streamlit(report)
        elif diff_btn:
            st.warning("Please fill in all fields.")

    else:
        st.markdown("Compare the latest filings of two different companies.")
        col1, col2 = st.columns(2)
        with col1:
            cmp_ticker_a = st.text_input("Ticker A", placeholder="AAPL", key="cmp_ticker_a").strip().upper()
        with col2:
            cmp_ticker_b = st.text_input("Ticker B", placeholder="MSFT", key="cmp_ticker_b").strip().upper()
        cmp_filing_type = st.selectbox(
            "Filing Type", options=["10-K", "10-Q", "8-K"], key="cmp_filing_type"
        )
        cmp_btn = st.button("Compare Companies", type="primary", key="cmp_btn")

        if cmp_btn and cmp_ticker_a and cmp_ticker_b:
            with st.spinner("Comparing companies..."):
                try:
                    from sec_filing_agent.diff.analyzer import compare_companies
                    report = run_async(compare_companies(
                        ticker_a=cmp_ticker_a,
                        ticker_b=cmp_ticker_b,
                        filing_type=cmp_filing_type,
                    ))
                except Exception as e:
                    st.error(f"Comparison failed: {e}")
                    st.stop()
            render_comparison_streamlit(report)
        elif cmp_btn:
            st.warning("Please enter both ticker symbols.")

# ── Tab: Trends ──────────────────────────────────────────────────────────────

with tab_trends:
    st.markdown("Multi-year financial trends using XBRL structured data.")
    col1, col2, col3 = st.columns([3, 1, 1])
    with col1:
        trend_ticker = st.text_input(
            "Ticker", placeholder="AAPL", key="trend_ticker"
        ).strip().upper()
    with col2:
        trend_years = st.number_input("Years", min_value=2, max_value=10, value=5, key="trend_years")
    with col3:
        trend_btn = st.button("Analyze Trends", type="primary", use_container_width=True, key="trend_btn")

    if trend_btn and trend_ticker:
        with st.spinner("Fetching XBRL financial data..."):
            try:
                from sec_filing_agent.trends import analyze_trends
                report = run_async(analyze_trends(ticker=trend_ticker, years=trend_years))
            except Exception as e:
                st.error(f"Trend analysis failed: {e}")
                st.stop()
        render_trends_chart(report)
    elif trend_btn:
        st.warning("Please enter a ticker symbol.")

# ── Tab: Sector ──────────────────────────────────────────────────────────────

with tab_sector:
    st.markdown("Compare a company against its sector peers using XBRL data.")
    col1, col2 = st.columns([3, 2])
    with col1:
        sector_ticker = st.text_input(
            "Ticker", placeholder="AAPL", key="sector_ticker"
        ).strip().upper()
    with col2:
        sector_peers_raw = st.text_input(
            "Custom Peers (optional, comma-separated)",
            placeholder="MSFT, GOOG, META",
            key="sector_peers",
        )
    sector_btn = st.button("Analyze Sector", type="primary", key="sector_btn")

    if sector_btn and sector_ticker:
        peers = None
        if sector_peers_raw.strip():
            peers = [p.strip().upper() for p in sector_peers_raw.split(",") if p.strip()]

        with st.spinner("Fetching sector data..."):
            try:
                from sec_filing_agent.sector import analyze_sector
                report = run_async(analyze_sector(ticker=sector_ticker, peers=peers))
            except Exception as e:
                st.error(f"Sector analysis failed: {e}")
                st.stop()
        render_sector_streamlit(report)
    elif sector_btn:
        st.warning("Please enter a ticker symbol.")
