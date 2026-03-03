"""Agent SDK usage examples — the recommended way to use sec-filing-agent."""

import asyncio

from sec_filing_agent import Agent


async def main() -> None:
    agent = Agent()

    # Single analysis
    print("=== Single Analysis ===")
    report = await agent.analyze("AAPL", filing_type="10-K")
    print(f"{report.ticker}: {report.summary[:100]}...")
    print(f"Cost: ${report.model_usage.estimated_cost_usd:.3f}")

    # Batch analysis
    print("\n=== Batch Analysis ===")
    reports = await agent.analyze_batch(["AAPL", "MSFT"])
    for r in reports:
        print(f"{r.ticker}: {r.filing_type} — {r.summary[:80]}...")

    # Streaming
    print("\n=== Streaming ===")
    async for stage in agent.analyze_stream("NVDA"):
        if stage.status == "started":
            print(f"  Starting: {stage.name}...")
        elif stage.status == "completed" and stage.name != "complete":
            dur = f" ({stage.duration_s:.1f}s)" if stage.duration_s else ""
            print(f"  Done: {stage.name}{dur}")

    # Diff (compare same company over time)
    print("\n=== Diff Mode ===")
    diff = await agent.diff("AAPL", from_period="2023", to_period="2024")
    print(f"Changes: {diff.diff.summary[:100]}...")

    # Compare two companies
    print("\n=== Compare Mode ===")
    comp = await agent.compare("AAPL", "MSFT")
    print(f"Comparison: {comp.comparison.summary[:100]}...")


if __name__ == "__main__":
    asyncio.run(main())
