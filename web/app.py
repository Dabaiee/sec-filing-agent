"""Streamlit web app for SEC Filing Intelligence Agent."""

from __future__ import annotations

import asyncio
import time
from datetime import date

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
    st.markdown("---")
    st.markdown("### Model Usage")
    usage = report.model_usage
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Tokens", f"{usage.total_input_tokens + usage.total_output_tokens:,}")
    with col2:
        st.metric("Estimated Cost", f"${usage.estimated_cost_usd:.3f}")
    with col3:
        st.metric("Pipeline Duration", f"{report.pipeline_duration_ms:,}ms")

    if usage.stages:
        with st.expander("Per-stage breakdown"):
            for stage in usage.stages:
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


# --- Main App ---

st.title("📊 SEC Filing Intelligence Agent")
st.markdown(
    "AI-powered analysis of SEC filings. Get structured risk assessments, "
    "financial highlights, and event summaries from 10-K, 10-Q, and 8-K filings."
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
        "Built with [sec-filing-agent](https://github.com/your-username/sec-filing-agent)"
    )

# Input row
col_input, col_type, col_btn = st.columns([2, 2, 1])
with col_input:
    ticker = st.text_input(
        "Ticker Symbol",
        placeholder="AAPL",
        max_chars=10,
        label_visibility="collapsed",
    ).strip().upper()
with col_type:
    filing_type = st.selectbox(
        "Filing Type",
        options=["Latest Available", "10-K", "10-Q", "8-K"],
        label_visibility="collapsed",
    )
with col_btn:
    analyze_btn = st.button("Analyze", type="primary", use_container_width=True)

# Analysis
if analyze_btn and ticker:
    selected_type = None if filing_type == "Latest Available" else filing_type

    # Progress container
    progress_container = st.container()
    progress_items = []

    def update_progress(stage_id: str, status: str, message: str) -> None:
        progress_items.append((stage_id, status, message))

    with st.spinner("Running analysis pipeline..."):
        try:
            report = run_async(run_analysis(ticker, selected_type, update_progress))
        except Exception as e:
            st.error(f"Analysis failed: {e}")
            st.stop()

    # Show pipeline progress
    with progress_container:
        st.markdown("#### Pipeline Progress")
        for _stage_id, status, message in progress_items:
            if status == "done":
                st.markdown(f"✅ {message}")
            else:
                st.markdown(f"🔄 {message}")

    # Render report
    render_report(report)

    # Download buttons
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
