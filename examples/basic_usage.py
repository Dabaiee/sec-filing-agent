"""Basic usage example for SEC Filing Agent."""

import asyncio

from sec_filing_agent import analyze, fetch_filing


async def main() -> None:
    # Fetch and analyze the latest 10-K for Apple
    report = await analyze("AAPL", filing_type="10-K")

    print(f"Company: {report.company_name}")
    print(f"Filing: {report.filing_type} ({report.filing_date})")
    print(f"Summary: {report.summary}")

    if report.financial_highlights:
        print(f"\nRevenue: {report.financial_highlights.revenue}")
        print(f"Net Income: {report.financial_highlights.net_income}")

    if report.risk_factors:
        print(f"\nTop Risk Factors:")
        for rf in report.risk_factors[:3]:
            print(f"  [{rf.severity.upper()}] {rf.title}")

    print(f"\nTokens used: {report.model_usage.total_input_tokens + report.model_usage.total_output_tokens}")
    print(f"Estimated cost: ${report.model_usage.estimated_cost_usd:.3f}")


if __name__ == "__main__":
    asyncio.run(main())
